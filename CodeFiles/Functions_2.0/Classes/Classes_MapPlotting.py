#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader


class MapPlotting:
    def __init__(self, sw_corner, ne_corner, delta=5, fontsize=5):
        """
        Initialize a BoundingBoxPlotter object.

        Parameters
        ----------
        sw_corner : tuple
            (lat_min, lon_min) of the bounding box (southwest corner).
        ne_corner : tuple
            (lat_max, lon_max) of the bounding box (northeast corner).
        delta : float
            Half-width (in degrees) of the plotted area around the box center.
        fontsize : int
            Font size for province labels.
        """
        self.lat_min, self.lon_min = sw_corner
        self.lat_max, self.lon_max = ne_corner
        self.delta = delta
        self.fontsize = fontsize

        # Precompute center of bounding box
        self.center_lat = (self.lat_min + self.lat_max) / 2
        self.center_lon = (self.lon_min + self.lon_max) / 2

        # Natural Earth provinces shapefile
        shapename = 'admin_1_states_provinces'
        self.shpfilename = shpreader.natural_earth(
            resolution='10m', category='cultural', name=shapename
        )

    def PlotBoundingBox(self):
        """Plot the bounding box and provinces inside the map extent."""
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(subplot_kw={"projection": proj}, figsize=(10, 8))

        # Base map
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.6)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        # Bounding box
        ax.add_patch(Rectangle(
            (self.lon_min, self.lat_min),
            self.lon_max - self.lon_min,
            self.lat_max - self.lat_min,
            fill=False, edgecolor='red', linewidth=2,
            transform=ccrs.PlateCarree(), label="Bounding Box"
        ))

        # Set extent centered on bounding box
        ax.set_extent(
            [self.center_lon - self.delta, self.center_lon + self.delta,
             self.center_lat - self.delta, self.center_lat + self.delta]
        )

        # Provinces
        reader = shpreader.Reader(self.shpfilename)
        xmin, xmax, ymin, ymax = ax.get_extent(crs=ccrs.PlateCarree())

        for record in reader.records():
            geom = record.geometry
            name = record.attributes["name"]
            admin = record.attributes["admin"]
            x, y = geom.centroid.x, geom.centroid.y

            # Only show provinces within plot extent
            if xmin <= x <= xmax and ymin <= y <= ymax:
                ax.add_geometries([geom], crs=ccrs.PlateCarree(),
                                  facecolor='none', edgecolor='gray', linewidth=0.5)
                ax.text(x, y, f"{name} ({admin})", fontsize=self.fontsize,
                        ha="center", va="center", transform=ccrs.PlateCarree(),
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, lw=0))
# # --- Example usage ---
# plotter = MapPlotting(
#     sw_corner=(24.46, 121.00),  # (lat_min, lon_min)
#     ne_corner=(24.83, 123.10),  # (lat_max, lon_max)
#     delta=5,
#     fontsize=5
# )
# plotter.PlotBoundingBox()


