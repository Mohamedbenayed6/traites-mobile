# Traites Bancaires — Application mobile (Android)

Version téléphone de votre application de gestion des traites : mêmes
champs, mêmes positions d'impression mesurées sur la vraie kembyela, même
logique. Pour l'instant, ses données sont **indépendantes** de
l'application de bureau (pas encore synchronisées — ce sera la prochaine
étape une fois que celle-ci fonctionne bien).

## Comment ça marche

- **Nouvelle traite, Archive, Clients, Rapports, Calibrage** : les mêmes
  écrans que sur PC, adaptés à l'écran du téléphone.
- **Impression** : l'application génère le PDF de la traite, puis
  l'envoie à l'application **Epson iPrint** (à installer séparément
  depuis le Play Store) pour l'impression via le Wi-Fi de l'imprimante —
  exactement comme vous me l'avez décrit.
- **Données** : stockées uniquement sur le téléphone pour l'instant.

---

## Étape 1 — Créer le fichier APK

Comme les outils de construction Android ne sont pas accessibles depuis
l'environnement où j'ai préparé ce projet, la construction du fichier
APK se fait automatiquement **sur les serveurs de GitHub** (gratuit),
via un système appelé *GitHub Actions*. Vous n'avez rien à installer sur
votre ordinateur pour cette étape.

### 1.1 Créer un compte GitHub (si vous n'en avez pas)

Allez sur [github.com](https://github.com) → "Sign up" → suivez les
étapes (gratuit).

### 1.2 Créer un nouveau dépôt (repository)

1. Une fois connecté, cliquez sur le **+** en haut à droite → **"New
   repository"**.
2. Donnez-lui un nom, par exemple `traites-mobile`.
3. Laissez-le en **Public** (nécessaire pour la construction automatique
   gratuite) ou en Private si vous préférez (fonctionne aussi, avec un
   quota d'utilisation gratuit largement suffisant pour ce projet).
4. Cliquez sur **"Create repository"**.

### 1.3 Envoyer les fichiers du projet

1. Sur la page de votre nouveau dépôt (vide), cliquez sur **"uploading an
   existing file"** (ou "Add file" → "Upload files").
2. Ouvrez le dossier `TraiteMobile` que je vous ai fourni, **sélectionnez
   tous les fichiers et dossiers à l'intérieur** (pas le dossier
   `TraiteMobile` lui-même, son *contenu*), et glissez-les dans la page
   GitHub.
   - Important : le dossier caché `.github` (qui contient les
     instructions de construction) doit aussi être envoyé. S'il
     n'apparaît pas dans le glisser-déposer de votre explorateur de
     fichiers (les dossiers commençant par un point sont parfois
     cachés), activez l'affichage des fichiers cachés, ou utilisez
     GitHub Desktop (voir note ci-dessous) qui envoie tout
     automatiquement.
3. Cliquez sur **"Commit changes"** en bas de la page.

> **Astuce plus simple si vous êtes à l'aise avec ça** : installez
> [GitHub Desktop](https://desktop.github.com/), connectez votre compte,
> "Add local repository" en choisissant le dossier `TraiteMobile`, puis
> "Publish repository". Cela envoie tout, y compris les fichiers cachés,
> sans réfléchir aux détails.

### 1.4 Suivre la construction automatique

1. Sur votre dépôt GitHub, cliquez sur l'onglet **"Actions"** en haut.
2. Vous devriez voir une construction ("Construire l'APK") démarrer
   automatiquement après l'envoi des fichiers. Si ce n'est pas le cas,
   cliquez sur "Construire l'APK" dans la liste à gauche puis sur le
   bouton **"Run workflow"**.
3. Cliquez dessus pour voir la progression. **La première construction
   prend environ 15 à 25 minutes** (elle télécharge et prépare tous les
   outils Android) — les suivantes seront plus rapides.
4. Une fois terminé (coche verte ✅), cliquez sur la construction
   terminée, puis tout en bas dans la section **"Artifacts"**, cliquez
   sur **"TraitesBancaires-apk"** pour télécharger un fichier `.zip`
   contenant votre APK.

Si la construction échoue (croix rouge ❌), cliquez dessus pour voir le
message d'erreur — envoyez-le-moi et je corrigerai.

---

## Étape 2 — Installer l'APK sur le téléphone de votre père

1. Transférez le fichier `.apk` (extrait du zip téléchargé) sur le
   téléphone (par e-mail à vous-même, WhatsApp, câble USB, Google
   Drive...).
2. Sur le téléphone, ouvrez le fichier `.apk` depuis l'application
   Fichiers / Téléchargements.
3. Android va probablement afficher un avertissement du type "Installation
   d'applications inconnues bloquée" — c'est normal pour toute application
   qui n'est pas installée depuis le Play Store. Appuyez sur
   **"Paramètres"** dans ce message, activez **"Autoriser depuis cette
   source"**, puis revenez en arrière et appuyez de nouveau sur le
   fichier APK pour l'installer.
4. Une fois installée, l'application **"Traites Bancaires"** apparaît
   sur l'écran d'accueil / dans le tiroir d'applications.

---

## Étape 3 — Premier lancement

1. Ouvrez l'application. Le menu (☰ en haut à gauche) donne accès à
   tous les écrans.
2. Allez dans **Calibrage impression** pour vérifier que tout est prêt —
   les positions sont déjà les mêmes que sur l'application de bureau
   (mesurées sur la vraie kembyela), donc ça devrait déjà être bon.
3. Créez une traite de test (**Nouvelle traite**), enregistrez, puis
   essayez **"Enregistrer + Imprimer"**.

### Comment l'impression se déroule concrètement

L'application essaie d'envoyer directement le PDF à Epson iPrint via le
sélecteur de partage Android. **Cette étape n'a pas pu être testée sur un
vrai téléphone de mon côté** (je n'ai accès qu'à un environnement de
développement, pas à un appareil Android réel) — il est donc possible
qu'elle ne fonctionne pas du premier coup selon la version d'Android.
C'est pour ça qu'il y a **toujours un filet de sécurité** : quoi qu'il
arrive, le PDF est enregistré dans un dossier accessible, et l'application
vous affiche un message indiquant où le trouver. Dans ce cas :

1. Ouvrez **Epson iPrint**.
2. Choisissez **"Imprimer Photos ou Documents"** (ou équivalent selon la
   version de l'app).
3. Naviguez jusqu'au dossier indiqué dans le message (généralement
   *Téléchargements/Traites*) et sélectionnez le fichier PDF de la
   traite.
4. Imprimez via le Wi-Fi, comme d'habitude.

Si le partage direct fonctionne bien chez vous du premier coup, tant
mieux — sinon, dites-le-moi et on pourra l'améliorer une fois qu'on peut
observer ce qui se passe réellement sur le téléphone.

---

## Notes techniques (pour information)

- **Pourquoi KivyMD 1.2.0 et pas la dernière version ?** La version la
  plus récente (2.0) vient tout juste de sortir et son comportement
  n'est pas encore assez fiable pour être testé avec confiance de mon
  côté. La 1.2.0 est une version stable et largement utilisée.
- **Emplacement des données sur le téléphone** :
  `Android/data/org.benayed.traitesbancaires/files/traite.db` (dossier
  propre à l'application, jamais supprimé sauf si vous désinstallez
  l'app).
- **Sauvegarde** : pensez à copier ce fichier de temps en temps (via un
  gestionnaire de fichiers) sur un ordinateur ou un cloud, en attendant
  la version synchronisée.

## Étape suivante (plus tard)

Une fois que cette version fonctionne bien pour vous, on pourra ajouter
la synchronisation avec l'application de bureau (base de données
partagée en ligne), comme discuté. On n'a pas besoin de tout refaire —
seulement d'ajouter une couche de synchronisation par-dessus ce qui
existe déjà.
