"""The splat tab's map and panorama previews. The 3D viewer itself is
streetview_to_3d's, the same one the street tab uses."""
from streetview_to_3d.ui.viewers import iframe


MAP_PLACEHOLDER = iframe(
    "<html><body style='margin:0;background:#1e1e2e;color:#777;font:14px sans-serif;"
    "display:flex;align-items:center;justify-content:center;height:100vh'>"
    "Load a location to see it on the map</body></html>",
    aspect="16/9",
)
PANO_PLACEHOLDER = iframe(
    "<html><body style='margin:0;background:#111;color:#777;font:14px sans-serif;"
    "display:flex;align-items:center;justify-content:center;height:100vh'>"
    "Panorama viewer</body></html>"
)
def build_map(lat: float, lon: float) -> str:
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body,#map{{margin:0;height:100%;width:100%}}</style>
</head><body><div id="map"></div>
<script>
var m = L.map('map').setView([{lat},{lon}], 18);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',
    {{maxZoom:22,maxNativeZoom:19,attribution:'© OpenStreetMap'}}).addTo(m);
L.circleMarker([{lat},{lon}],{{radius:9,color:'crimson',fillColor:'crimson',fillOpacity:0.9,weight:2}}).addTo(m);
</script></body></html>"""
    return iframe(doc)


def build_pano_viewer(img_url: str) -> str:
    doc = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>body{{margin:0;background:#000;overflow:hidden;cursor:grab}}body:active{{cursor:grabbing}}canvas{{display:block}}
#hint{{position:fixed;bottom:8px;right:8px;color:rgba(255,255,255,.4);font:11px sans-serif;pointer-events:none}}</style>
<script type="importmap">
{{"imports":{{"three":"https://unpkg.com/three@0.178.0/build/three.module.js"}}}}
</script></head><body><div id="hint">drag to look around</div>
<script type="module">
import * as THREE from 'three';
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, innerWidth/innerHeight, 0.01, 1000);
const renderer = new THREE.WebGLRenderer({{antialias:true}});
renderer.setPixelRatio(devicePixelRatio);
renderer.setSize(innerWidth, innerHeight);
document.body.appendChild(renderer.domElement);
const geo = new THREE.SphereGeometry(100, 64, 32); geo.scale(-1,1,1);
const mat = new THREE.MeshBasicMaterial();
scene.add(new THREE.Mesh(geo, mat));
new THREE.TextureLoader().load('{img_url}', t => {{ t.colorSpace=THREE.SRGBColorSpace; mat.map=t; mat.needsUpdate=true; }});
renderer.outputColorSpace = THREE.SRGBColorSpace;

let lon = 0, lat = 0, dragging = false, lx = 0, ly = 0;
renderer.domElement.addEventListener('pointerdown', e => {{ dragging = true; lx = e.clientX; ly = e.clientY; }});
addEventListener('pointerup', () => dragging = false);
addEventListener('pointermove', e => {{
    if (!dragging) return;
    lon -= (e.clientX - lx) * 0.2; lat += (e.clientY - ly) * 0.2;
    lat = Math.max(-85, Math.min(85, lat));
    lx = e.clientX; ly = e.clientY;
}});
renderer.domElement.addEventListener('wheel', e => {{
    e.preventDefault();
    camera.fov = Math.max(20, Math.min(100, camera.fov + e.deltaY * 0.05));
    camera.updateProjectionMatrix();
}}, {{passive:false}});

addEventListener('resize', () => {{
    camera.aspect = innerWidth/innerHeight; camera.updateProjectionMatrix();
    renderer.setSize(innerWidth, innerHeight);
}});
const tick = () => {{
    const phi = THREE.MathUtils.degToRad(90 - lat);
    const theta = THREE.MathUtils.degToRad(lon);
    camera.lookAt(
        100 * Math.sin(phi) * Math.cos(theta),
        100 * Math.cos(phi),
        100 * Math.sin(phi) * Math.sin(theta),
    );
    renderer.render(scene, camera);
}};
renderer.setAnimationLoop(tick);
document.addEventListener('visibilitychange', () => {{
    renderer.setAnimationLoop(document.hidden ? null : tick);
}});
</script></body></html>"""
    return iframe(doc)
