import torch
import torch.nn as nn
import numpy as np

# Using NIPALS algorithm.
class PLSDA(nn.Module):
    def __init__(self, num_bands, num_classes, max_iter=1e3, num_lv=40, threshold=1e-6, progress_manager=None, dtype=np.float32, device="cpu"):
        super().__init__()
        self.max_iter = max_iter
        self.num_lv = num_lv  # number of latent variables
        self.threshold = threshold
        self.progress_manager = progress_manager
        self.dtype=dtype
        self.device = device

        self.T = None
        self.P = None
        self.W = None
        self.U = None
        self.Q = None
        self.B = torch.Tensor(num_bands, num_classes)
        self.b = np.zeros(num_lv).astype(dtype)

    def forward(self, x):
        return torch.mm(x.squeeze() / 4095.0, self.B)

    def fit(self, X, Y):
        X = X.squeeze() / 4095.0
        n = X.shape[0]
        m = X.shape[1]
        p = Y.shape[1]

        assert X.shape[0] == Y.shape[0], "Incompatible X and Y matrices"

        self.T = np.zeros((n, self.num_lv)).astype(self.dtype)
        self.P = np.zeros((m, self.num_lv)).astype(self.dtype)
        self.W = np.zeros((m, self.num_lv)).astype(self.dtype)
        self.U = np.zeros((n, self.num_lv)).astype(self.dtype)
        self.Q = np.zeros((p, self.num_lv)).astype(self.dtype)

        self.b = np.zeros(self.num_lv).astype(self.dtype)

        # Start with maximal residual (matrix X, matrix Y)
        x = X.copy()
        y = Y.copy()
        
        # Loop for each possible latent variable
        for i in range(self.num_lv):
            # Initialize u as a column of x with maximum variance
            u = y[:, np.argmax(np.sum(np.power(y, 2), axis=0))].copy()

            for _ in range(int(self.max_iter)):
                # Weight vector (Normalized)
                w = np.dot(x.T, u) / np.dot(u, u)
                w /= np.linalg.norm(w)

                # Common Score
                t = np.dot(x, w)

                # Y loading (Normalized)
                q = np.dot(y.T, t) / np.dot(t, t)
                q /= np.linalg.norm(q)

                # Evaluate _u as projection of q in y
                _u = np.dot(y, q)

                u_delta = _u - u
                u = _u
                if np.dot(u_delta, u_delta) < self.threshold:
                    # self.progress_manager.progress(overwrite=n + (i + 1) * self.max_iter)
                    break

            # Save the evaluated values
            p = np.dot(x.T, t) / np.dot(t, t)
            p_norm = np.linalg.norm(p)
            p = p / p_norm
            t = t * p_norm
            w = w * p_norm

            # Regression coefficient for the inner relation
            self.b[:self.num_lv][i] = np.dot(u.T, t) / np.dot(t, t)

            # Calculate residuals
            x -= np.dot(np.row_stack(t), np.column_stack(p))
            y -= self.b[:self.num_lv][i] * np.dot(np.row_stack(t), np.column_stack(q.T))

            self.P[:, :self.num_lv][:, i] = p
            self.T[:, :self.num_lv][:, i] = t
            self.W[:, :self.num_lv][:, i] = w
            self.U[:, :self.num_lv][:, i] = u
            self.Q[:, :self.num_lv][:, i] = q
            
            self.progress_manager.step()

        self.B = torch.from_numpy(((self.W.dot(np.linalg.inv(self.P.T.dot(self.W)))).dot(np.diag(self.b))).dot(self.Q.T)).to(self.device)