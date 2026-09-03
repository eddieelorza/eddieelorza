# Setup — 5 minutos

## 0. El repo

Tu README de perfil vive en un repo **con el mismo nombre que tu usuario**:

```
github.com/<tu-usuario>/<tu-usuario>
```

Si no existe: créalo público, marca "Add a README file". Si ya existe, solo copia estos archivos encima.

## 1. Copia todo

```
README.md
assets/                 ← 8 SVG animados (dark + light)
scripts/build_assets.py ← generador (los SVG salen de aquí)
scripts/personalize.sh
.github/workflows/snake.yml
.github/workflows/build-assets.yml
```

## 2. Pon tu usuario

```bash
bash scripts/personalize.sh tu-usuario-github
```

Eso reemplaza el placeholder `USERNAME` en los links de stats, streak, activity graph y snake.

## 3. Commit

```bash
git add -A
git commit -m "feat: animated profile README"
git push
```

## 4. Enciende el snake

Ve a **Actions → Generate contribution snake → Run workflow**.
Al terminar crea una rama `output` con `snake-dark.svg` y `snake-light.svg`.
El README ya apunta ahí. Después corre solo cada 12 h.

> Si Actions está deshabilitado en el repo: Settings → Actions → General → *Allow all actions*.
> Y en **Workflow permissions** elige *Read and write permissions*.

---

## Cómo funciona (para que puedas tocarlo)

### Los SVG son tuyos, no de un servicio

`scripts/build_assets.py` es la única fuente de verdad. Arriba tiene el diccionario `THEMES`
con los design tokens. Cambia un hex ahí y regenera:

```bash
python3 scripts/build_assets.py
```

Salen las 8 variantes (dark + light de hero, pipeline, focus, divider). El workflow
`build-assets.yml` hace lo mismo automáticamente cuando editas el script y lo pusheas.

### Por qué animan dentro de GitHub

GitHub sirve las imágenes a través de su proxy (camo) como `<img>`. En ese contexto:

| Técnica | ¿Funciona? |
|---|---|
| CSS `@keyframes` dentro del `<svg>` | ✅ |
| SMIL (`<animate>`, `<animateMotion>`, `<animateTransform>`) | ✅ |
| `<script>` / JS | ❌ (ignorado) |
| Fuentes externas (`@import`, Google Fonts) | ❌ (usa font stacks del sistema) |

Por eso el hero usa CSS para las entradas y SMIL para el movimiento y los dots que viajan por
la red neuronal: es lo más compatible entre Chrome, Firefox y Safari.

### Dark / light real

```html
<picture>
  <source media="(prefers-color-scheme: dark)"  srcset="./assets/hero-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/hero-light.svg">
  <img alt="…" src="./assets/hero-dark.svg" width="100%">
</picture>
```

GitHub respeta `prefers-color-scheme` según **el tema de GitHub del visitante**, no el del SO.
Las tarjetas de stats usan `bg_color=00000000` (transparente), así que sirven en ambos temas
sin duplicar.

> **Si por alguna razón las rutas relativas no cargan** en tu repo, corre
> `bash scripts/personalize.sh tu-usuario --raw` y las convierte a URLs
> `raw.githubusercontent.com`.

### Caché de imágenes

Camo cachea agresivamente. Si actualizas un SVG y no ves el cambio, añade un query string:
`./assets/hero-dark.svg?v=2`.

---

## Opcional: métricas avanzadas (lowlighter/metrics)

Requiere un PAT clásico con scope `read:user` guardado como secret `METRICS_TOKEN`.
Crea `.github/workflows/metrics.yml`:

```yaml
name: Metrics
on:
  schedule: [{ cron: "0 6 * * *" }]
  workflow_dispatch:
permissions:
  contents: write
jobs:
  metrics:
    runs-on: ubuntu-latest
    steps:
      - uses: lowlighter/metrics@latest
        with:
          token: ${{ secrets.METRICS_TOKEN }}
          filename: assets/metrics.svg
          base: header, activity, community, repositories
          config_timezone: America/Mexico_City
          plugin_languages: yes
          plugin_languages_details: bytes-size, percentage
          plugin_isocalendar: yes
          config_output: svg
```

Y en el README: `<img src="./assets/metrics.svg" width="100%">`.

---

## Checklist antes de publicar

- [ ] Repo se llama exactamente como tu usuario y es **público**
- [ ] `personalize.sh` corrido (no queda ningún `USERNAME` en el README)
- [ ] Actions con *Read and write permissions*
- [ ] Workflow `snake` corrido una vez → existe la rama `output`
- [ ] Abre tu perfil en tema claro **y** oscuro y verifica el hero
- [ ] Ábrelo en móvil: el hero es `width="100%"`, debe escalar sin cortarse
- [ ] Los links (portfolio, LinkedIn, mail) apuntan a donde deben
