"""Native effects for pre-admitted explicit N10 geometry and camera."""

import numpy as np


def apply_camera(ax, camera):
    if any(
        v is not None
        for v in (camera.elevation, camera.azimuth, camera.roll, camera.vertical_axis)
    ):
        ax.view_init(
            camera.elevation, camera.azimuth, camera.roll, camera.vertical_axis or "z"
        )
    if camera.projection is not None or camera.focal_length is not None:
        ax.set_proj_type(camera.projection or "persp", focal_length=camera.focal_length)
    if camera.box_aspect is not None or camera.zoom is not None:
        ax.set_box_aspect(
            camera.box_aspect, zoom=1 if camera.zoom is None else camera.zoom
        )


def _bars(ax, columns, layer, cfg, color):
    x, y, z, dx, dy, dz = (
        np.asarray(columns[name], dtype=float)
        for name in (layer.x, layer.y, layer.z, cfg.dx, cfg.dy, cfg.dz)
    )
    end = z + dz
    had_data = ax.has_data()
    xy_box, z_box = ax.xy_dataLim.frozen(), ax.zz_dataLim.frozen()
    # Keep original signed endpoints. Unshaded planar faces avoid lighting
    # reversed winding on native cuboids whose signed height is negative.
    artist = ax.bar3d(x, y, z, dx, dy, dz, color=color, alpha=layer.alpha, shade=False)
    ax.xy_dataLim.set(xy_box)
    ax.zz_dataLim.set(z_box)
    ax.auto_scale_xyz(
        [x.min(), (x + dx).max()],
        [y.min(), (y + dy).max()],
        [min(z.min(), end.min()), max(z.max(), end.max())],
        had_data,
    )
    return artist


def _contours(ax, layer, cfg, x, y, z, options):
    direction = cfg.direction or "z"
    # Native rotate_axes selects physical (Y,Z; X), (Z,X; Y) or (X,Y; Z).
    draw = ax.contour if layer.type == "contour3d" else ax.contourf
    if layer.line_width is not None:
        options["linewidths"] = layer.line_width
    if cfg.offset is None:
        return draw(x, y, z, levels=layer.levels, zdir=direction, **options)
    had_data = ax.has_data()
    xy_box, z_box = ax.xy_dataLim.frozen(), ax.zz_dataLim.frozen()
    artist = draw(
        x, y, z, levels=layer.levels, zdir=direction, offset=cfg.offset, **options
    )
    ax.xy_dataLim.set(xy_box)
    ax.zz_dataLim.set(z_box)
    a = [x[0, 0], x[0, -1]]
    b = [y[0, 0], y[-1, 0]]
    p = [cfg.offset, cfg.offset]
    t = [z.min(), z.max()]
    bounds = {"x": (p, b, t), "y": (a, p, t), "z": (a, b, p)}[direction]
    ax.auto_scale_xyz(*bounds, had_data)
    return artist


def draw_spatial(ax, spec, layer, color_iter):
    from ._render import _continuous_cmap

    cfg, kind = layer.spatial, layer.type
    if kind == "bar3d":
        return _bars(ax, spec.data.columns, layer, cfg, layer.color or next(color_iter))
    if kind == "voxels":
        filled = np.asarray(cfg.occupancy, dtype=bool).transpose(2, 1, 0)
        edges = ()
        if cfg.x_coords is not None:
            edges = (
                np.asarray(cfg.x_coords, dtype=float)[:, None, None],
                np.asarray(cfg.y_coords, dtype=float)[None, :, None],
                np.asarray(cfg.z_coords, dtype=float)[None, None, :],
            )
        options = {} if layer.line_width is None else {"linewidth": layer.line_width}
        return ax.voxels(
            *edges,
            filled,
            facecolors=layer.color or next(color_iter),
            edgecolors=layer.edge_color,
            alpha=layer.alpha,
            shade=True,
            **options,
        )

    z = np.asarray(spec.data.matrices[layer.matrix], dtype=float)
    x, y = np.meshgrid(
        np.asarray(cfg.x_coords, dtype=float),
        np.asarray(cfg.y_coords, dtype=float),
        copy=False,
    )
    if kind == "wireframe":
        return ax.plot_wireframe(
            x,
            y,
            z,
            rstride=1,
            cstride=1,
            color=layer.color or next(color_iter),
            alpha=layer.alpha,
        )
    options = {"cmap": _continuous_cmap(layer.cmap_kind), "alpha": layer.alpha}
    if kind == "surface":
        artist = ax.plot_surface(x, y, z, rstride=1, cstride=1, **options)
    else:
        artist = _contours(ax, layer, cfg, x, y, z, options)
    if layer.colorbar:
        ax.figure.colorbar(artist, ax=ax, label=layer.clabel or "")
    return artist
