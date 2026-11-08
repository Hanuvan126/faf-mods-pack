"""Rebuild only GGA1401 geometry and SCM previews; leave materials/animation intact."""
from PIL import Image, ImageDraw
from generate_caldera import ASSETS, UNIT, NAMES, PARENTS, PIVOTS, build_mesh
from reactor_geometry import export_obj, render_scm
from supcom_binary import write_scm


def main():
    for lod, detail in ((0, 28), (1, 12)):
        mesh = build_mesh(detail)
        path = UNIT / f'GGA1401_lod{lod}.scm'
        write_scm(mesh, path, NAMES, PARENTS, PIVOTS)
        if lod == 0:
            export_obj(mesh, ASSETS, NAMES)
        print(f'LOD{lod}: {len(mesh.vertices)} vertices, {len(mesh.indices)//3} triangles', flush=True)

    views = []
    for name, azimuth, elevation in (('Front', 0, 16), ('Side', 90, 16), ('Game', 35, 38)):
        path = ASSETS / f'GGA1401_optimized_{name.lower()}.png'
        im = render_scm(UNIT/'GGA1401_lod0.scm', ASSETS, path, azimuth, elevation,
                        (.13, .78, .42), 700, texture_mip=1)
        ImageDraw.Draw(im).text((15, 15), name, fill=(220, 232, 240))
        views.append(im)
    sheet = Image.new('RGB', (2100, 700))
    for i, im in enumerate(views):
        sheet.paste(im, (700*i, 0))
    sheet.save(ASSETS/'GGA1401_optimized_views.png')
    render_scm(UNIT/'GGA1401_lod1.scm', ASSETS, ASSETS/'GGA1401_optimized_lod1.png',
               35, 38, (.13, .78, .42), 700, texture_mip=2)


if __name__ == '__main__':
    main()
