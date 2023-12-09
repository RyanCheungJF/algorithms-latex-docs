import time
import pandas as pd
import numpy as np

from plotnine import *
from resizeable_image import ResizeableImage


ITERATIONS=100
runtimes = pd.DataFrame(index=np.arange(2 * ITERATIONS), columns=['algorithm','runtime'])

for i in range(ITERATIONS):
    image = ResizeableImage("images/sunset_full.png")
    t0 = time.time()
    image.best_seam(True)
    t1 = time.time()
    runtimes.iloc[i]['runtime'] = t1 - t0
    runtimes.iloc[i]['algorithm'] = 'dp'
    
    # t0 = time.time()
    # image.best_seam(False)
    # t1 = time.time()
    # runtimes.iloc[ITERATIONS + i]['runtime'] = t1 - t0
    # runtimes.iloc[ITERATIONS + i]['algorithm'] = 'naive'
    
runtimes['runtime'] = runtimes['runtime'].astype(float)

p = ggplot(runtimes, aes(x='algorithm', y='runtime')) + geom_boxplot()
print(p)
