#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader


class MapPlotting:
    def __init__(self, sw_corner=None, ne_corner=None, delta=5, fontsize=5):
        """
        Initialize a map plotting object.

        Parameters
        ----------
        sw_corner : tuple or None
            (lat_min, lon_min) of the bounding box (optional).
        ne_corner : tuple or None
            (lat_max, lon_max) of the bounding box (optional).
        delta : float
            Default half-width (degrees) around bounding box center.
        fontsize : int
            Font size for province labels.
        """
        self.lat_min, self.lon_min = (None, None)
        self.lat_max, self.lon_max = (None, None)
        self.delta = delta
        self.fontsize = fontsize

        if sw_corner and ne_corner:
            self.lat_min, self.lon_min = sw_corner
            self.lat_max, self.lon_max = ne_corner
            self.center_lat = (self.lat_min + self.lat_max) / 2
            self.center_lon = (self.lon_min + self.lon_max) / 2
        else:
            self.center_lat, self.center_lon = (None, None)

        # Natural Earth provinces shapefile
        shapename = "admin_1_states_provinces"
        self.shpfilename = shpreader.natural_earth(
            resolution="10m", category="cultural", name=shapename
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
            fill=False, edgecolor="red", linewidth=2,
            transform=ccrs.PlateCarree(), label="Bounding Box"
        ))

        # Set extent centered on bounding box
        ax.set_extent(
            [self.center_lon - self.delta, self.center_lon + self.delta,
             self.center_lat - self.delta, self.center_lat + self.delta]
        )

        # Provinces
        self._add_provinces(ax)

    def PlotMap(self, center_lat, center_lon, dlat, dlon):
        """
        Plot a map centered on (lat, lon), extending dlat/dlon degrees.

        Parameters
        ----------
        center_lat : float
            Center latitude.
        center_lon : float
            Center longitude.
        dlat : float
            Half-width in latitude degrees.
        dlon : float
            Half-width in longitude degrees.
        """
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(subplot_kw={"projection": proj}, figsize=(10, 8))

        # Base map
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.6)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        # Set extent
        ax.set_extent([
            center_lon - dlon, center_lon + dlon,
            center_lat - dlat, center_lat + dlat
        ])

        # Provinces
        self._add_provinces(ax)

    def _add_provinces(self, ax):
        """Helper: add provinces inside current extent."""
        reader = shpreader.Reader(self.shpfilename)
        xmin, xmax, ymin, ymax = ax.get_extent(crs=ccrs.PlateCarree())

        for record in reader.records():
            geom = record.geometry
            name = record.attributes["name"]
            admin = record.attributes["admin"]
            x, y = geom.centroid.x, geom.centroid.y

            # Only show provinces within extent
            if xmin <= x <= xmax and ymin <= y <= ymax:
                ax.add_geometries([geom], crs=ccrs.PlateCarree(),
                                  facecolor="none", edgecolor="gray", linewidth=0.5)
                ax.text(x, y, f"{name} ({admin})", fontsize=self.fontsize,
                        ha="center", va="center", transform=ccrs.PlateCarree(),
                        bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.5, lw=0))

    def PlotFromBounds(self, lat_min, lat_max, lon_min, lon_max):
        """
        Plot a map over the specified latitude/longitude bounds.

        Parameters
        ----------
        lat_min, lat_max : float
            Latitude range in degrees.
        lon_min, lon_max : float
            Longitude range in degrees.
        """
        proj = ccrs.PlateCarree()
        fig, ax = plt.subplots(subplot_kw={"projection": proj}, figsize=(10, 8))

        # Base map
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=":", linewidth=0.6)
        ax.gridlines(draw_labels=True, linestyle="--", alpha=0.5)

        # Set extent directly from bounds
        ax.set_extent([lon_min, lon_max, lat_min, lat_max])

        # Provinces
        self._add_provinces(ax)

        return fig, ax
