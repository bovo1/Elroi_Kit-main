"""
    ELROILAB Kit

    Copyright 2026. Elroilab All rights reserved.
"""

import numpy as np

def calculateSimilarity(data, ref, mode):
    """
        description: Calculate pixel-based similarity between data and reference using specified mode
        parameters:
            data: numpy array of shape (H, W, C) - input image data
            ref: numpy array of shape (C,) - reference pixel values
            mode: string - similarity mode ("Area", "Cosine", "SAM", "L2", "Chebyshev", "Canberra", "Jeffrey", "GLE")
        returns:
            similarity_map: numpy array of shape (H, W) with similarity values in range [0, 100]
        author : Hyunsu Kim (2026.05.19)
    """
    eps = 1e-10
    originShape = data.shape[:2]
    flatData = data.reshape(-1, data.shape[-1])

    if mode == "Area":
        diff = np.abs(ref - flatData)
        max_vals = np.max(np.maximum(ref, flatData), axis=1)
        denom = np.maximum(max_vals * flatData.shape[1], eps)
        sim = (1.0 - (np.sum(diff, axis=1) / denom)) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "Cosine":
        ref_norm = np.linalg.norm(ref) + eps
        data_norm = np.linalg.norm(flatData, axis=1) + eps
        sim = ((np.sum(flatData * ref, axis=1) / (ref_norm * data_norm)) + 1) * 50.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "SAM":
        ref_norm = ref / (np.linalg.norm(ref) + eps)
        data_norm = flatData / (np.linalg.norm(flatData, axis=1, keepdims=True) + eps)
        cos_theta = np.clip(np.sum(data_norm * ref_norm[None, :], axis=1), -1.0, 1.0)
        theta = np.arccos(cos_theta)
        sim = (1.0 - (theta / (np.pi / 2))) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "L2":
        dist = np.linalg.norm(flatData - ref, axis=1)
        maxd = np.sqrt(np.sum(np.maximum(ref, flatData) ** 2, axis=1))
        sim = (1.0 - (dist / np.maximum(maxd, eps))) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "Chebyshev":
        dist = np.max(np.abs(ref - flatData), axis=1)
        max_dist = np.max(np.maximum(ref, flatData), axis=1)
        sim = (1.0 - (dist / np.maximum(max_dist, eps))) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "Canberra":
        num = np.abs(ref - flatData)
        den = np.maximum(ref + flatData, eps)
        canb = np.sum(num / den, axis=1)
        max_d = np.max(
            np.maximum(np.abs(ref) / den, np.abs(flatData) / den),
            axis=1,
        )
        dist = canb / np.maximum(max_d * flatData.shape[1], eps)
        sim = (1.0 - dist) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)

    if mode == "Jeffrey":
        kl_pq = ref * np.log((ref + eps) / (flatData + eps))
        kl_qp = flatData * np.log((flatData + eps) / (ref + eps))
        pair_div = kl_pq + kl_qp
        jdiv = np.sum(pair_div, axis=1)
        max_jdiv = np.max(pair_div, axis=1)
        sim = (1.0 - (jdiv / np.maximum(max_jdiv * flatData.shape[1], eps))) * 100.0
        return np.reshape(np.clip(sim, 0.0, 100.0), originShape)
    
    if mode == "GLE":
        epsilon=1e-8
        alpha=0.3
        beta=0.3
        gamma=0.4
        bands = flatData.shape[1]
        similarity_score = 0

        # 1. RMSE 계산
        diff = np.abs(flatData - ref)
        max_val = np.maximum(flatData, ref) + epsilon
        relative_diff = diff / max_val
        rmse = np.sqrt(np.mean(relative_diff ** 2, axis=-1))
        # 2. Linf (최대 차이) 계산
        linf_diff = np.max(diff, axis=-1) / (np.max(max_val, axis=-1) + epsilon)
        # 3. 동적 비선형 보정 (구간 내 차이 강조)
        adjusted_diff = np.log1p(diff) / np.log1p(max_val)
        nonlinear_score = np.sqrt(np.mean((adjusted_diff) ** 2,axis=-1))
        # 4. 세그먼트 유사도 계산 (가중 조합) gle : rmse(alpha) / nonlinear(beta) / linf(gamma)
        segment_similarity = (alpha * (1 - rmse) + beta *  (1 - nonlinear_score) + gamma * (1 - linf_diff))
        similarity_score += segment_similarity
        similarity = similarity_score * 100
        similarity = np.reshape(similarity, originShape)
        return similarity

    raise ValueError(f"Unknown similarity mode: {mode}")
