#!/usr/bin/env python

import matplotlib.pyplot as plt

colormaps = ('viridis', 'inferno', 'magma', 'jet', 'binary')
for c in colormaps:
    cmap_name = c
    cmap = plt.get_cmap(cmap_name)

    colors = [[int(round(255 * x)) for x in cmap(i)[:3]] for i in range(256)]
    print(f'var {c} = {colors}')

print(f'var colormaps = [{", ".join(colormaps)}];')
