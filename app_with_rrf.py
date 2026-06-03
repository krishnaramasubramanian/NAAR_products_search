from flask import Flask, render_template, request, jsonify
import asyncio
import pandas as pd
import traceback
import logging
from vector_search.query import search as pinecone_search
from fuzzy.meilisearch_search import search as meilisearch_search
from rrf_utils import RRFusion
from query_correction.query_corrector import correct_query

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# CloudFront URL for images
CLOUDFRONT_URL = "https://d1rr3f1zok8deh.cloudfront.net/uploads/products/"

# Load products CSV for image filenames
products_df = pd.read_csv('products.csv')
products_dict = {str(row['_id']): row['fileName'] for _, row in products_df.iterrows()}


@app.route('/')
def index():
    return render_template('index_rrf.html')


@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json
    query = data.get('query', '').strip()
    fusion_method = data.get('fusion_method', 'rrf')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    if len(query.split()) < 3:
        logger.info(f"Query has < 3 words, applying correction. Original: '{query}'")
        query = correct_query(query)
        logger.info(f"After correction: '{query}'")
    else:
        logger.info(f"Query has >= 3 words, skipping correction. Query: '{query}'")
    
    try:
        logger.info(f"Query: {query}, Fusion method: {fusion_method}")
        
        # Get results from both sources
        logger.info(f"Calling pinecone_search with query: '{query}'")
        pinecone_results = asyncio.run(pinecone_search(query, top_k=10, min_score=0.35))
        logger.info(f"Pinecone results count: {len(pinecone_results)}")
        logger.debug(f"Pinecone results: {pinecone_results}")
        
        logger.info(f"Calling meilisearch_search with query: '{query}'")
        meilisearch_results = meilisearch_search(query, top_k=25)
        logger.info(f"MeiliSearch results count: {len(meilisearch_results)}")
        logger.debug(f"MeiliSearch results: {meilisearch_results}")
        
        # Convert to dictionaries for RRF processing
        logger.info("Converting Pinecone results to dictionaries...")
        pinecone_data = [{
            'title': r.title,
            'seller': r.seller,
            'product_id': r.product_id,
            'score': r.score
        } for r in pinecone_results]
        logger.debug(f"Pinecone data sample: {pinecone_data[:1] if pinecone_data else 'empty'}")
        
        logger.info("Converting MeiliSearch results to dictionaries...")
        meilisearch_data = [{
            'title': r.title,
            'seller': r.seller,
            'product_id': r.product_id,
            'score': r.score
        } for r in meilisearch_results]
        logger.debug(f"MeiliSearch data sample: {meilisearch_data[:1] if meilisearch_data else 'empty'}")
        
        # Apply fusion method
        fused_results = None
        weights = None
        
        if fusion_method == 'rrf':
            fused_results = RRFusion.rrf([pinecone_data, meilisearch_data])
        
        elif fusion_method == 'weighted_rrf':
            pinecone_weight = 0.2
            meili_weight = 0.8
            
            fused_results = RRFusion.weighted_rrf(
                [pinecone_data, meilisearch_data],
                weights=[pinecone_weight, meili_weight],
                min_score = 0.0025
            )
            weights = {
                "pinecone": pinecone_weight,
                "meilisearch": meili_weight
            }
        
        elif fusion_method == 'normalized_score_rrf':
            fused_results = RRFusion.normalized_score_rrf([pinecone_data, meilisearch_data])
        
        else:
            # Return separate results
            def get_product_id_str(pid):
                if isinstance(pid, (int, float)):
                    return str(int(pid))
                return str(pid)
            
            return jsonify({
                'fusion_method': 'separate',
                'pinecone': [
                    {
                        'title': r['title'],
                        'seller': r['seller'],
                        'product_id': r['product_id'],
                        'image_url': CLOUDFRONT_URL + products_dict.get(get_product_id_str(r['product_id']), ''),
                        'score': round(r['score'], 2)
                    } for r in pinecone_data
                ],
                'meilisearch': [
                    {
                        'title': r['title'],
                        'seller': r['seller'],
                        'product_id': r['product_id'],
                        'image_url': CLOUDFRONT_URL + products_dict.get(get_product_id_str(r['product_id']), ''),
                        'score': round(r['score'], 2)
                    } for r in meilisearch_data
                ]
            })
        
        logger.debug(f"Fused results count: {len(fused_results)}")
        logger.debug(f"Fused results sample: {fused_results[:1] if fused_results else 'None'}")
        
        # Build final results with defensive checks
        final_results = []
        for r in fused_results:
            try:
                # Defensive: check if product_id exists and convert to string
                product_id = r.get('product_id')
                if not product_id:
                    logger.warning(f"Missing product_id in result: {r}")
                    continue
                
                # Handle both string (MongoDB ObjectId) and numeric product_ids
                if isinstance(product_id, (int, float)):
                    product_id_str = str(int(product_id))
                else:
                    product_id_str = str(product_id)
                filename = products_dict.get(product_id_str, '')
                image_url = CLOUDFRONT_URL + filename if filename else ''
                
                result_item = {
                    'title': r.get('title', 'N/A'),
                    'seller': r.get('seller', 'N/A'),
                    'product_id': str(product_id),
                    'image_url': image_url,
                    'score': round(r.get('rrf_score', r.get('score', 0)), 2)
                }
                final_results.append(result_item)
            except Exception as item_error:
                logger.error(f"Error processing individual result: {r}, Error: {str(item_error)}")
                continue
        
        response = {
            'fusion_method': fusion_method,
            'results': final_results
        }
        
        if weights:
            response['weights'] = weights
        
        logger.info(f"Returning {len(final_results)} results")
        return jsonify(response)
    
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return jsonify({'error': str(e), 'details': traceback.format_exc()}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)