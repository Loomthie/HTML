import numpy as np

tl = np.array([8,12,16,20])
fl = np.array([1.25,1.12,1.05,1.00])

fl_y = fl*tl
fl_x = np.array([tl,np.ones_like(tl),-fl]).T

res_fl = np.linalg.solve(fl_x.T @ fl_x, fl_x.T @ fl_y)
res_fl[1] -= res_fl[0] * res_fl[2]


def fl_corr(L):
    return res_fl[0] + res_fl[1] / (L + res_fl[2])