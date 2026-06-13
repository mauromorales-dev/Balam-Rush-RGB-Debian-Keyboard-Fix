# 💡 Balam Rush RGB Controller (Linux)

Pequeña aplicación en Python + GTK para controlar la iluminación RGB de teclados **Balam Rush / Acteck México** en Linux (Debian y derivados).

Este proyecto surge porque muchos de estos teclados no tienen soporte oficial en Linux, lo que deja el RGB deshabilitado por defecto.

---

## 🚀 ¿Qué hace este proyecto?

- Detecta automáticamente el teclado por USB (`vendor/product ID`)
- Accede al dispositivo mediante `/dev/hidraw`
- Envía comandos directos al firmware del teclado
- Permite encender / apagar el RGB desde una interfaz gráfica
- Configura permisos automáticamente con `udev`
- Opción de auto-inicio con sesión del sistema

---

## 🧠 ¿Cómo funciona?

Linux no cuenta con drivers RGB oficiales para este teclado, por lo que el sistema lo expone como un dispositivo HID genérico.

Este proyecto:
- Localiza el dispositivo HID correcto
- Escribe bytes directamente al hardware
- Interactúa con el firmware del teclado a bajo nivel

👉 No se usa software del fabricante  
👉 No hay API oficial  
👉 Comunicación directa con el dispositivo

---

## 🛠️ Requisitos

Instala dependencias en Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3-gi gir1.2-gtk-3.0
