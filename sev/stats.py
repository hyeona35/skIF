from __future__ import annotations
import math, random
from dataclasses import dataclass

@dataclass
class PairedStats:
    n: int
    mean_delta: float
    std_delta: float
    ci_low: float
    ci_high: float
    win_rate: float
    significance: bool
    improvement_significant: bool
    method: str = 'paired_bootstrap'

def paired_bootstrap(deltas, iterations=2000, alpha=0.05, seed=7):
    xs=[float(x) for x in deltas]
    if not xs:return PairedStats(0,0,0,0,0,0,False,False)
    mean=sum(xs)/len(xs); var=sum((x-mean)**2 for x in xs)/max(1,len(xs)-1); std=math.sqrt(var)
    rng=random.Random(seed); means=[]; n=len(xs)
    for _ in range(max(200,iterations)): means.append(sum(xs[rng.randrange(n)] for _ in range(n))/n)
    means.sort(); lo=means[min(len(means)-1,max(0,int((alpha/2)*len(means))))]; hi=means[min(len(means)-1,max(0,int((1-alpha/2)*len(means))-1))]
    return PairedStats(n,mean,std,lo,hi,sum(x>0 for x in xs)/n,lo>0 or hi<0,lo>0)
