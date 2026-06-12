# Google Drive folder setup (one time, ~3 minutes)

The dashboard's **📁 + Drive folder** button creates a folder for each topic inside a
date folder in your Google Drive:

```
AI x Ahmad Content / 2026-06-12 / Gemini 3 launch video /
```

The folder is shared "anyone with the link can edit", so your editors can upload
footage, posters and exports straight into it.

## Steps

1. Open https://script.google.com → **New project**
2. Delete the sample code and paste this:

```javascript
const ROOT = "AI x Ahmad Content";

function doGet(e) {
  const topic = (e.parameter.topic || "Untitled").replace(/[\\/:*?"<>|]/g, "-").slice(0, 80);
  const date = (e.parameter.date || Utilities.formatDate(new Date(), "Asia/Karachi", "yyyy-MM-dd"));
  const root = getOrMake(DriveApp.getRootFolder(), ROOT);
  const day  = getOrMake(root, date);
  const f    = getOrMake(day, topic);
  f.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.EDIT);
  return ContentService.createTextOutput(JSON.stringify({ url: f.getUrl() }))
    .setMimeType(ContentService.MimeType.JSON);
}

function getOrMake(parent, name) {
  const it = parent.getFoldersByName(name);
  return it.hasNext() ? it.next() : parent.createFolder(name);
}
```

3. Click **Deploy → New deployment** → gear icon → **Web app**
   - Description: anything
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy**, authorize with your Google account (it will warn the app is
     unverified — click *Advanced → Go to project*; it is your own script).
4. Copy the **Web app URL** (looks like `https://script.google.com/macros/s/AKfy.../exec`).
5. In the dashboard, click **📁 + Drive folder** on any task and paste that URL when
   asked. That's it — the URL is saved and synced to your editors automatically.

## Notes

- Folders are created in **your** Drive; editors get edit access via the link.
- If you redeploy the script, the URL changes — paste the new one when asked
  (clear the old one by rejecting the prompt and re-running setup).
- The button turns green ("📁 Open Drive folder") once a task has its folder.
