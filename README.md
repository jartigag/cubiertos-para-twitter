# 🍴 cubiertos para twitter

He diseñado mi propia *cubertería* con el objetivo de **hacer que *digerir* Twitter sea más fácil**.

### **tenedor**
> “Comer bocado a bocado”

De un @username, extrae **métricas** generales, ratios y tops, *para después enviar un **informe por md** (#wip)*  
(basado en [tweet_analyzer (x0rz)](https://github.com/x0rz/tweets_analyzer))

<p align="center"><a href="https://asciinema.org/a/QTjDYRC4k4pp0ewyfLQlKTmfD" target="_blank"><img src="https://asciinema.org/a/QTjDYRC4k4pp0ewyfLQlKTmfD.png" width="50%"/></a></p>

### **cuchillo**
> “Separar la carne del hueso”

**Unfollow** @username si no está en whitelist, no followback y ha estado activo/inactivo por n días

<p align="center"><a href="https://asciinema.org/a/IQFOlDY4RMWFdtuHWK4Pz4k7k" target="_blank"><img src="https://asciinema.org/a/IQFOlDY4RMWFdtuHWK4Pz4k7k.png" width="50%"/></a></a></p>

### **cazo**
> “Servir de la olla al plato”

**Agrega** @username de fuentes{keyword,followersoffollowers} **a lista privada** si cumple parámetros

<p align="center"><a href="https://asciinema.org/a/U1UdjaSvK12VPI5OkYmRF8qm7" target="_blank"><img src="https://asciinema.org/a/U1UdjaSvK12VPI5OkYmRF8qm7.png" width="50%"/></a></p>

 ## ##
La analogía con unos utensilios conocidos como son los cubiertos pretende sugerir de manera intuitiva para qué sirve cada una de estas herramientas y cuál es su finalidad general: ayudar al usuario, ya sea ofreciéndole **información** relevante o **automatizando algunas rutinas**. Pero, tal y como ocurre con los cubiertos, deben emplearse de forma auxiliar. Es decir, estos scripts no realizan ninguna acción en nombre del usuario (ni publicar, ni seguir, ni RTs ni Likes) porque se quiere evitar que el perfil personal del usuario se convierta en una cuenta bot e impersonal. Tan sólo se hacen unfollows con `cuchillo.py` si el usuario así lo confirma, y la lista de Twitter sobre la que trabaja `cazo.py` es privada para que el usuario filtre de forma manual qué perfiles de los recogidos en ella le interesan.
