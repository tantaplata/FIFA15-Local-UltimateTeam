# FIFA 15 Local FUT — Preservation Archive (Public Test 1 / v0.2.39)

> [!IMPORTANT]
> **ARCHIVE NOTICE / PRESERVATION MIRROR (AS-IS)**
> This repository is an unmaintained historical archive and preservation mirror. The original repository and author disappeared / were taken down, so this copy was preserved and re-uploaded for archival purposes. 
> - **No new commits, feature additions, or active maintenance will be made.**
> - The files are provided "as-is" for personal preservation, testing, and research.
>
> *(Para la versión en español, desplázate hacia abajo o consulta la sección al final).*

---

## ⚠️ REQUIRED: Download Large External Files

GitHub enforces a strict 100 MB file size limit, meaning the heavy FIFA `.big` game archives cannot be committed directly to Git. They are bundled in an external archive:

📦 **Download:** `archivos_grandes_fifa15.zip` *(~383 MB compressed / ~425 MB uncompressed)*  
🔗 **Download link:** *(Upload `archivos_grandes_fifa15.zip` to your GitHub Releases or external host, e.g. Google Drive / Mega / MediaFire, and place the link here)*

### How to install them:

#### Option 1: Quick Install (Recommended)
1. Download `archivos_grandes_fifa15.zip`.
2. Move it to the **root directory** of this repository (the same folder containing `PLAY_LOCAL_FUT15.cmd`).
3. Right-click and choose **"Extract Here"** (Extraer aquí).
   - Because the ZIP preserves relative folder paths, every file will automatically land in its exact required destination!

#### Option 2: Manual Placement
If you extract files individually, place each file into its designated directory:

| File | Size | Destination Folder |
| :--- | :--- | :--- |
| `data_patch.big` | 150.47 MB | `payload\data_patch.big` |
| `cards0.big` | 51.71 MB | `payload\cards0.big` |
| `locale.big` | 45.64 MB | `payload\data\loc\locale.big` |
| `data_startup.big` | 26.46 MB | `payload\data_startup.big` |
| `data_patch.big` *(Original backup)* | 150.47 MB | `original-client-db-before-legends\data_patch.big` |

Once those files are in place, the launcher will work as intended. See [`LARGE_FILES_INSTRUCTIONS.txt`](LARGE_FILES_INSTRUCTIONS.txt) for more details.

---

## Quick start

1. Extract the project to a normal folder (for example, Downloads or Games).
2. Ensure the large files mentioned above are extracted/copied into their folders.
3. Run **`INSTALL_PREREQUISITES.cmd`** once. It checks/installs Python, the required Python package, and the Visual C++ runtime used by the FIFA 15 Cards DLL.
4. Run **`PLAY_LOCAL_FUT15.cmd`**. On first run it finds your FIFA 15 installation, backs up files it replaces, installs the Local FUT payload, creates desktop shortcuts, starts the localhost services, and launches FIFA 15.
5. Future launches can use the **FIFA 15 Local FUT** desktop shortcut.

> This requires your own installed copy of FIFA 15 PC. The project is intended for local/offline restoration testing; it does not connect to EA's retired FUT service.

---

## Fresh starter club

A brand-new Local FUT save starts intentionally small:

- **0 coins** by default.
- **14 bronze Premier League players** only (including a usable mix of GK/DEF/MID/ST positions).
- One active **Arsenal badge**.
- **Arsenal home + away kits**.
- One starter **stadium** (Sanderson Park).
- One starter **ball** so matches have a complete club identity.
- One starter squad, with additional squads supported.

FUT will still let the player choose/confirm their own club name. Club progress, coins, squads, items and Transfer List state are persisted in:

`%LOCALAPPDATA%\FIFA15LocalFUT\fut15-local.sqlite3`

If you previously used a development build and want to test the exact fresh-public state, run **`RESET_TO_STARTER_CLUB.cmd`**. It only deletes the Local FUT database; it does not delete normal Career/Settings saves.

The modern Admin Panel also provides **Tools → Delete club and start fresh**. It creates a dated SQLite backup, closes FIFA, stops only the Local FUT server process, deletes the Local FUT club save and then confirms when it is safe to relaunch.

---

## Daily reward packs

The Admin Panel Overview includes a **Daily reward** card while the Local FUT server is running. One reward can be claimed per local calendar day. Consecutive claims advance through a seven-day pack ladder: Gold, Premium Gold, Rare Gold, Premium Gold Players, Mega, Rare Players, then Jumbo Rare Players. Reward cards use the normal pack generator and appear in Unassigned Items; existing Unassigned Items must be cleared before claiming.

---

## Open Transfer Market price range

User listings can use any valid start price and Buy Now price from **150 to 15,000,000 coins**, regardless of the card's suggested AI-market value. The local AI buyer still considers its internal valuation when deciding whether and how quickly to purchase an expensive listing.

The local market can also place a visible AI bid on an active listing. A bid is never below the card's stored market valuation and can be up to 8% higher, provided the user's starting price is not above the offer. Press **Y** on the Transfer List entry to view the received offer. Competitive Buy Now listings can still sell immediately; otherwise a winning AI bid settles when the auction expires and the normal 5% tax applies.

Transfer Targets are persisted in the local save. Adding a watched card, placing a bid, buying a card or submitting a card offer automatically adds that auction to Transfer Targets; removing it clears the saved target.

---

## Optional test coins

Run **`ADD_COINS.cmd`** and enter how many local coins you want to add. The default is 1,000,000 coins. This modifies only the localhost FUT SQLite balance.

---

## Admin Centre edition

Run **`ADMIN_MENU.cmd`** to open the graphical Local FUT admin centre. It can:

- Set or add coins and FIFA Points on the active local save.
- Change the club name, abbreviation and manager name.
- Create, duplicate, enable, disable and delete store packs.
- Adjust pack prices, contents, rarity, tier weights, special-card odds and a guaranteed minimum player rating live.
- Configure the local AI Transfer Market and offline modes.
- Back up the Local FUT save, open logs and safely reset the club.

Balance and pack edits are read by the running server. Refresh the relevant FUT screen after saving. Core server/market configuration changes apply on the next launch.

---

## What is included

- Persistent local FUT club/profile.
- Store and pack opening, including promo packs.
- FIFA 15 player database and special-card pack pools.
- Club consumables.
- Badge/kit/stadium/ball support.
- Transfer List lifecycle, relisting, sold-item clearing and quick sell.
- Large deterministic local AI Transfer Market and local AI buyers for user listings.
- Multiple squads.
- Offline Seasons work from the current development line.
- Port auto-remapping for local FIFA services where possible.

---

## About `ItsAMe_Origin.dll`

The filename is intentionally left unchanged. It is part of the compatibility chain used by this build and its exact filename is embedded in the binary, so renaming it just for presentation could break startup on clean machines.

The launcher backs up existing client files before installing the payload. Use `RESTORE_BACKUP.cmd` if you want to return to the original files.

---
---

# 🇪🇸 Versión en Español

> [!IMPORTANT]
> **AVISO DE ARCHIVO / COPIA DE PRESERVACIÓN (TAL CUAL)**
> Este repositorio es un archivo histórico y réplica de preservación sin mantenimiento activo. El repositorio original fue eliminado/dado de baja de internet, por lo que esta copia fue guardada y resubida con fines de preservación.
> - **No se realizarán nuevos commits, mejoras de funciones ni mantenimiento activo.**
> - Todo el contenido se proporciona "tal cual" (*as-is*) para preservación y uso personal.

---

## ⚠️ OBLIGATORIO: Descargar los archivos pesados externos

GitHub tiene un límite estricto de 100 MB por archivo, por lo que los archivos `.big` pesados del juego no pueden subirse directamente a Git. Están empaquetados en un archivo comprimido externo:

📦 **Archivo:** `archivos_grandes_fifa15.zip` *(~383 MB comprimido / ~425 MB descomprimido)*  
🔗 **Enlace de descarga:** *(Sube `archivos_grandes_fifa15.zip` a tus GitHub Releases o servicio externo como Google Drive / Mega / MediaFire y coloca aquí el enlace)*

### Cómo instalarlos:

#### Opción 1: Instalación Rápida (Recomendada)
1. Descarga `archivos_grandes_fifa15.zip`.
2. Cópialo en la **carpeta raíz** de este repositorio (donde se encuentra `PLAY_LOCAL_FUT15.cmd`).
3. Haz clic derecho y elige **"Extraer aquí"** (Extract Here).
   - Como el ZIP conserva la estructura original de carpetas, cada archivo se colocará automáticamente en su lugar exacto.

#### Opción 2: Colocación Manual
Si prefieres extraer los archivos por separado, colócalos en las siguientes rutas dentro del proyecto:

| Archivo | Tamaño | Carpeta de Destino |
| :--- | :--- | :--- |
| `data_patch.big` | 150.47 MB | `payload\data_patch.big` |
| `cards0.big` | 51.71 MB | `payload\cards0.big` |
| `locale.big` | 45.64 MB | `payload\data\loc\locale.big` |
| `data_startup.big` | 26.46 MB | `payload\data_startup.big` |
| `data_patch.big` *(Copia original)* | 150.47 MB | `original-client-db-before-legends\data_patch.big` |

Para más detalles, consulta [`INSTRUCCIONES_ARCHIVOS_GRANDES.txt`](INSTRUCCIONES_ARCHIVOS_GRANDES.txt).

---

## Inicio rápido

1. Extrae el proyecto en una carpeta normal (por ejemplo, Descargas o Juegos).
2. Asegúrate de haber extraído/colocado los archivos pesados mencionados arriba.
3. Ejecuta **`INSTALL_PREREQUISITES.cmd`** una sola vez. Verifica e instala Python, paquetes requeridos y el runtime de Visual C++.
4. Ejecuta **`PLAY_LOCAL_FUT15.cmd`**. En la primera ejecución detectará tu FIFA 15, creará un respaldo de seguridad de los archivos originales, instalará los archivos del servidor local, creará accesos directos en el escritorio y abrirá el juego.
5. En los siguientes inicios podrás entrar directamente desde el acceso directo de escritorio **FIFA 15 Local FUT**.

---

## Panel de Administración (Admin Centre)

Ejecuta **`ADMIN_MENU.cmd`** para abrir el panel gráfico del servidor local. Permite:
- Añadir o modificar monedas y FIFA Points.
- Modificar el nombre del club y manager.
- Crear, duplicar y configurar sobres de la tienda (probabilidades, medias mínimas garantizadas, precios).
- Configurar el mercado de transferencias simulado por IA.
- Respaldar partidas o reiniciar el club de forma segura.
