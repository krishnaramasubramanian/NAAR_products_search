from collections import defaultdict
from typing import List, Dict, Any, Optional
import math


class RRFusion:
    """Reciprocal Rank Fusion for combining multiple ranked result sets."""
    
    @staticmethod
    def rrf(results_list: List[List[Dict[str, Any]]], k: int = 60, weights: Optional[List[float]] = None, min_score: float = 0.0) -> List[Dict[str, Any]]:
        """
        Standard RRF: score = sum(1 / (k + rank))
        
        Args:
            results_list: List of result lists from different sources
            k: RRF constant (typically 60)
            weights: Optional weights for each result list (must sum to 1.0)
            min_score: Minimum RRF score to include (filtering before rounding)
        
        Returns:
            Fused results sorted by RRF score
        """
        if weights is None:
            weights = [1.0 / len(results_list)] * len(results_list)
        
        rrf_scores = defaultdict(float)
        item_info = {}
        
        for source_idx, results in enumerate(results_list):
            for rank, item in enumerate(results, 1):
                item_id = str(item.get('product_id'))
                if item_id:
                    rrf_scores[item_id] += weights[source_idx] * (1 / (k + rank))
                    
                    if item_id not in item_info:
                        item_info[item_id] = item.copy()
                        item_info[item_id]['sources'] = []
                    
                    item_info[item_id]['sources'].append({
                        'source': source_idx,
                        'rank': rank,
                        'original_score': item.get('score')
                    })
        
        # Build final results - filter BEFORE rounding
        fused = []
        for item_id, rrf_score in rrf_scores.items():
            # Filter first using actual calculated value
            if rrf_score >= min_score:
                result = item_info[item_id]
                result['rrf_score'] = round(rrf_score, 4)
                fused.append(result)
        
        fused.sort(key=lambda x: x['rrf_score'], reverse=True)
        return fused
    
    @staticmethod
    def weighted_rrf(results_list: List[List[Dict[str, Any]]], k: int = 60, weights: List[float] = None, min_score: float = 0.001) -> List[Dict[str, Any]]:
        if weights is None:
            weights = [1.0] * len(results_list)
        
        # Normalize weights
        total = sum(weights)
        normalized_weights = [w / total for w in weights]
        
        return RRFusion.rrf(results_list, k, normalized_weights, min_score)
    
    @staticmethod
    def bounded_rrf(results_list: List[List[Dict[str, Any]]], k: int = 60, top_n: int = 25, min_score: float = 0.01) -> List[Dict[str, Any]]:
        """
        Bounded RRF: Only consider top_n results from each source (more efficient).
        
        Args:
            results_list: List of result lists
            k: RRF constant
            top_n: Consider only top_n from each source
            min_score: Minimum RRF score to include in results
        
        Returns:
            Fused results
        """
        bounded_results = [results[:top_n] for results in results_list]
        return RRFusion.rrf(bounded_results, k, min_score=min_score)
    
    @staticmethod
    def normalized_score_rrf(results_list: List[List[Dict[str, Any]]], k: int = 60, min_score: float = 0.001) -> List[Dict[str, Any]]:
        """
        RRF with normalized original scores included in the fusion.
        Combines RRF ranking with normalized original scores.
        
        Args:
            results_list: List of result lists with 'score' field
            k: RRF constant
            min_score: Minimum combined score to include in results
        
        Returns:
            Fused results with combined score, filtered by minimum score
        """
        rrf_scores = defaultdict(float)
        normalized_scores = defaultdict(float)
        item_info = {}
        
        for results in results_list:
            # Find min/max scores for normalization
            scores = [item.get('score', 0) for item in results if item.get('score')]
            if scores:
                min_score_val = min(scores)
                max_score = max(scores)
                score_range = max_score - min_score_val if max_score != min_score_val else 1
            
            for rank, item in enumerate(results, 1):
                item_id = str(item.get('product_id'))
                if item_id:
                    # RRF component
                    rrf_scores[item_id] += 1 / (k + rank)
                    
                    # Normalized score component
                    if scores and 'score' in item:
                        normalized = (item['score'] - min_score_val) / score_range
                        normalized_scores[item_id] += normalized
                    
                    if item_id not in item_info:
                        item_info[item_id] = item.copy()
        
        # Combine both scores - filter BEFORE rounding
        fused = []
        for item_id in rrf_scores:
            combined = 0.7 * rrf_scores[item_id] + 0.3 * normalized_scores[item_id]
            
            # Filter first using actual calculated value
            if combined >= min_score:
                result = item_info[item_id]
                result['rrf_score'] = round(rrf_scores[item_id], 4)
                result['combined_score'] = round(combined, 4)
                fused.append(result)
        
        fused.sort(key=lambda x: x['combined_score'], reverse=True)
        return fused