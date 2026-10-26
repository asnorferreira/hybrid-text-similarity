import math
from dataclasses import asdict, dataclass

import numpy as np


def sigmoid(values):
    z = np.asarray(values,dtype=float)
    result = np.empty_like(z)
    positive = z >= 0
    result[positive] = 1/(1+np.exp(-z[positive]))
    negative_exp = np.exp(z[~positive])
    result[~positive] = negative_exp/(1+negative_exp)
    return result


def finite_scores(values):
    if type(values) is not list or not values or any(type(v) not in (int,float) or not math.isfinite(v) for v in values):
        raise ValueError('finite numeric scores required')
    return np.asarray(values, dtype=float)


def binary_targets(values, count):
    if type(values) is not list or len(values) != count or any(type(v) is not int or v not in (0,1) for v in values):
        raise ValueError('binary integer targets required')
    return np.asarray(values, dtype=float)


def regularized_targets(positive, negative):
    if any(type(v) is not int or v < 1 for v in (positive,negative)):
        raise ValueError('both classes required')
    return (positive+1)/(positive+2), 1/(negative+2)


def probabilities(A, B, scores):
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (A,B)):
        raise ValueError('finite calibration parameters required')
    x = finite_scores(scores)
    with np.errstate(over='ignore'):
        p = sigmoid(-A*x-B)
    return np.clip(p, np.nextafter(0.,1.), np.nextafter(1.,0.)).tolist()


def fit_platt(scores, targets):
    x = finite_scores(scores)
    if (x < 0).any() or (x > 1).any():
        raise ValueError('P1 fusion scores must be within [0,1]')
    y = binary_targets(targets, len(x))
    positive = int(y.sum()); negative = len(y)-positive
    t_positive, t_negative = regularized_targets(positive, negative)
    t = np.where(y == 1, t_positive, t_negative)
    def objective(params):
        z = params[0]*x+params[1]
        p = sigmoid(z); residual = p-t; weights = p*(1-p)
        hessian = np.asarray([[np.mean(weights*x*x),np.mean(weights*x)],[np.mean(weights*x),np.mean(weights)]])
        return (float(np.mean(np.logaddexp(0,z)-t*z)),
                np.asarray([np.mean(residual*x),np.mean(residual)]),hessian)
    params = np.asarray([1.,0.])
    for iteration in range(1000):
        value,gradient,hessian = objective(params)
        projected = gradient.copy()
        boundary = params[0] <= 1e-12 and gradient[0] > 0
        if boundary:projected[0]=0
        if np.max(np.abs(projected)) < 1e-9:break
        direction = -np.linalg.solve(hessian+np.eye(2)*1e-12,gradient)
        if boundary:direction=np.asarray([0.,-gradient[1]/max(hessian[1,1],1e-12)])
        for power in range(50):
            candidate = params+2.**(-power)*direction
            candidate[0] = max(1e-12,candidate[0])
            candidate_value = objective(candidate)[0]
            if candidate_value <= value+1e-4*float(gradient@(candidate-params))+1e-15:
                params=candidate
                break
        else:raise RuntimeError('calibration Newton line search failed')
    else:raise RuntimeError('calibration optimizer did not converge')
    if not np.isfinite(params).all():raise RuntimeError('nonfinite calibration parameters')
    return dict(A=-float(params[0]), B=-float(params[1]), positive=positive, negative=negative,
                t_positive=t_positive, t_negative=t_negative, objective=objective(params)[0], iterations=iteration)


@dataclass(frozen=True)
class ReliabilityBin:
    lower: float
    upper: float
    count: int
    mean_probability: float | None
    positive_rate: float | None


@dataclass(frozen=True)
class CalibrationMetrics:
    n: int
    brier: float
    log_loss: float
    ece: float
    bins: list[ReliabilityBin]
    f1_at_0_5: float


def calibration_metrics(targets, values):
    p = finite_scores(values)
    y = binary_targets(targets,len(p))
    if (p < 0).any() or (p > 1).any():
        raise ValueError('probabilities must be within [0,1]')
    clipped = np.clip(p, np.finfo(float).eps, 1-np.finfo(float).eps)
    bins: list[ReliabilityBin] = []
    ece = 0.
    for i in range(10):
        mask = (p >= i/10) & ((p <= 1) if i == 9 else (p < (i+1)/10))
        count = int(mask.sum())
        confidence = float(p[mask].mean()) if count else None
        rate = float(y[mask].mean()) if count else None
        if count:
            assert confidence is not None and rate is not None
            ece += count/len(y)*abs(confidence-rate)
        bins.append(ReliabilityBin(lower=i/10,upper=(i+1)/10,count=count,mean_probability=confidence,positive_rate=rate))
    predicted = p >= .5
    tp = int(((y == 1) & predicted).sum()); fp = int(((y == 0) & predicted).sum()); fn = int(((y == 1) & ~predicted).sum())
    return asdict(CalibrationMetrics(n=len(y),brier=float(np.mean((p-y)**2)),
                log_loss=float(-np.mean(y*np.log(clipped)+(1-y)*np.log1p(-clipped))),
                ece=float(ece),bins=bins,f1_at_0_5=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.))
