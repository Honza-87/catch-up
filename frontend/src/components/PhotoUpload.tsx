import { useState } from "react";

import { deletePhoto, uploadPhoto } from "../api/members";

export function PhotoUpload({
  photoUrl,
  onChange,
}: {
  photoUrl: string | null;
  onChange: (url: string | null) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const { photo_url } = await uploadPhoto(file);
      onChange(photo_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onRemove() {
    setBusy(true);
    try {
      await deletePhoto();
      onChange(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="row">
      <img className="avatar" src={photoUrl ?? undefined} alt="" />
      <div>
        <input type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} onChange={onPick} />
        {photoUrl && (
          <button type="button" className="secondary" disabled={busy} onClick={onRemove}>
            Remove
          </button>
        )}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
