Trabajo del área de diseño

Primero revisar el README para ver que deben instalar para levantar el BACKEND y FRONTEND

Comandos (el backend y frontend se hacen en terminales separados)

*INICIAR BACKEND*

.\backend\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --port 8000 --app-dir .\backend

La terminal debe permanecer abierta.

EJEMPLO:
PS C:\Users\sagea\Desktop\Proyecto de Google calendar\AvtoGC> .\backend\.venv\Scripts\Activate.ps1
(.venv) PS C:\Users\sagea\Desktop\Proyecto de Google calendar\AvtoGC> python -m uvicorn app.main:app --reload --port 8000 --app-dir .\backend

funciona bien cuando sale la siguiente respuesta:

INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:32811 - "OPTIONS /api/canvas/status HTTP/1.1" 200 OK

*INICIAR FRONTEND*

npm run dev

Resultado esperado:

VITE ready
Local: http://localhost:5173/

Abrir:

http://localhost:5173

La terminal debe permanecer abierta.



----------------------------------------------------INDICACIONES-----------------------------------------------------------
1. Archivos que normalmente modifica diseño

frontend/src/App.jsx
frontend/src/styles.css
frontend/components/
frontend/api/client.js
frontend/index.html

El backend solo debe modificarse cuando esa tarea haya sido asignada.

2. Revisar cambios antes de subir

No se olviden clonear desde el MAIN y crear sus ramas, una vez que tiene su diseño y suban sus evidencias en el chat se puede hacer merge. Caso contrario solo hagan pull request y esperan a que revisemos en conjunto. (revisar en README como se crea una rama)

git status
git diff

Evitar git add . si no se ha revisado qué archivos serán incluidos. 

Agregar solamente los archivos modificados:

git add frontend/src/App.jsx
git add frontend/src/styles.css
git add frontend/components/CanvasAccessForm.jsx

O varios a la vez:

git add frontend/src/App.jsx frontend/src/styles.css frontend/components/CanvasAccessForm.jsx

Revisar lo preparado:

git status
git diff --staged

3. Crear el commit

Ejemplos:

git commit -m "design: mejorar pantalla de conexión con Canvas"
git commit -m "design: adaptar dashboard a dispositivos móviles"
git commit -m "feat: agregar filtro visual de actividades"
git commit -m "fix: corregir alineación de botones"

4. Subir la rama

Primera vez:

git push -u origin design/nombre-del-cambio

Después:

git push

En GitHub crear un Pull Request:

base: main
compare: design/nombre-del-cambio

El Pull Request debe explicar:

Qué se modificó.

Qué pantallas se afectaron.

Cómo se probó.

Capturas antes y después, cuando sea un cambio visual.

No hacer push directo a main.

5. Mantener la rama actualizada

Antes de comenzar una nueva sesión:

git switch main
git pull origin main
git switch design/nombre-del-cambio
git merge main

Si aparecen conflictos, resolverlos dentro de la rama personal.

Después:

git add ARCHIVOS_RESUELTOS
git commit -m "merge: actualizar rama con cambios de main"
git push

6. Agregar una dependencia de frontend (OPCIONAL)

cd frontend
npm install nombre-del-paquete

Esto modifica:

frontend/package.json
frontend/package-lock.json

Ambos archivos deben subirse junto con el código que utiliza el paquete:

git add frontend/package.json frontend/package-lock.json
git add frontend/src/ARCHIVO_MODIFICADO.jsx
git commit -m "build: agregar dependencia nombre-del-paquete"
git push

No se sube frontend/node_modules/.

7. Agregar una dependencia de backend (OPCIONAL)

cd backend
.\.venv\Scripts\Activate.ps1
python -m pip install nombre-del-paquete

Agregar la dependencia y su versión a requirements.txt.

Subir únicamente:

git add requirements.txt
git add backend/app/ARCHIVO_MODIFICADO.py
git commit -m "build: agregar dependencia nombre-del-paquete"
git push

No se sube backend/.venv/.