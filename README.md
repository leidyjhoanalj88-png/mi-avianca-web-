# 🛫 Avianca Web — Deploy en Railway

## Archivos del proyecto
```
avianca-railway/
├── index.html        ← Tu página web completa
├── main.py           ← Servidor Python (FastAPI)
├── requirements.txt  ← Dependencias
├── Procfile          ← Instrucciones para Railway
└── README.md
```

---

## 🚀 Pasos para publicar en Railway

### 1. Crea una cuenta en Railway
👉 Ve a https://railway.app y regístrate con GitHub (es gratis)

### 2. Sube el proyecto a GitHub
- Ve a https://github.com y crea un repositorio nuevo (ej: `mi-avianca-web`)
- Sube todos estos archivos al repositorio

### 3. Conecta en Railway
- En Railway haz clic en **"New Project"**
- Selecciona **"Deploy from GitHub repo"**
- Elige tu repositorio `mi-avianca-web`
- Railway detecta automáticamente el `Procfile` y despliega solo ✅

### 4. ¡Listo! Tu web estará en una URL como:
```
https://mi-avianca-web.up.railway.app
```

---

## ⚡ Alternativa más rápida (sin GitHub)

Instala Railway CLI:
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

---

## 💡 Notas
- Railway da **500 horas gratis al mes** (plan Hobby)
- Para dominio propio (ej: miavianca.com) cuesta ~$1/mes en Railway
