#!/usr/bin/env python
# coding=utf-8
'''
Author: Liang Qing
Date:Thursday, March 30, 2017 PM04:20:29 HKT
Info:
'''
'''
======================
3D surface (color map)
======================

Demonstrates plotting a 3D surface colored with the coolwarm color map.
The surface is made opaque by using antialiased=False.

Also demonstrates using the LinearLocator and custom formatting for the
z axis tick labels.
'''

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import numpy as np

_fingers = np.loadtxt('finger_prints.map')
fingers = np.reshape(_fingers, np.size(_fingers))
#print fingers
finger0 = np.reshape(fingers[0 : : 4], (6, 6))
finger1 = np.reshape(fingers[1 : : 4], (6, 6))
finger2 = np.reshape(fingers[2 : : 4], (6, 6))
finger3 = np.reshape(fingers[3 : : 4], (6, 6))
#print finger0


fig = plt.figure()
ax = fig.gca(projection='3d')

# Make data.
X = np.arange(0, 6)
Y = np.arange(0, 6)
print X
X, Y = np.meshgrid(X, Y)
# Plot the surface.
surf0 = ax.plot_surface(X, Y, finger0, cmap=cm.coolwarm, linewidth=0, antialiased=False)
surf1 = ax.plot_surface(X, Y, finger1, cmap=cm.coolwarm, linewidth=0, antialiased=False)
surf2 = ax.plot_surface(X, Y, finger2, cmap=cm.coolwarm, linewidth=0, antialiased=False)
surf3 = ax.plot_surface(X, Y, finger3, cmap=cm.coolwarm, linewidth=0, antialiased=False)
# Customize the z axis.
#ax.set_zlim(-1.01, 1.01)
#ax.zaxis.set_major_locator(LinearLocator(10))
#ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

# Add a color bar which maps values to colors.
#fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()
'''
'''
