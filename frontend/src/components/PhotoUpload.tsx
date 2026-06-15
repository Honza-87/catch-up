import { useState } from "react";
import Cropper, { type Area } from "react-easy-crop";

import { deletePhoto, uploadPhoto } from "../api/members";
import { getCroppedBlob } from "../lib/cropImage";

export function PhotoUpload({
  photoUrl,
  onChange,
}: {
  photoUrl: string | null;
  onChange: (url: string | null) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // While cropping: object URL of the picked file + crop/zoom state.
  const [src, setSrc] = useState<string | null>(null);
  const [crop, setCrop] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [areaPixels, setAreaPixels] = useState<Area | null>(null);

  function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // let the same file be re-picked later
    if (!file) return;
    setError(null);
    setCrop({ x: 0, y: 0 });
    setZoom(1);
    setAreaPixels(null);
    setSrc(URL.createObjectURL(file));
  }

  function closeCropper() {
    if (src) URL.revokeObjectURL(src);
    setSrc(null);
    setAreaPixels(null);
  }

  async function onSave() {
    if (!src || !areaPixels) return;
    setBusy(true);
    setError(null);
    try {
      const blob = await getCroppedBlob(src, areaPixels);
      const file = new File([blob], "avatar.jpg", { type: "image/jpeg" });
      const { photo_url } = await uploadPhoto(file);
      onChange(photo_url);
      closeCropper();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  async function onRemove() {
    setBusy(true);
    setError(null);
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
        {error && !src && <p className="error">{error}</p>}
      </div>

      {src && (
        <div className="modal-overlay" role="dialog" aria-modal="true">
          <div className="modal">
            <p className="muted" style={{ marginTop: 0 }}>Drag to position, slide to zoom.</p>
            <div className="cropper-area">
              <Cropper
                image={src}
                crop={crop}
                zoom={zoom}
                aspect={1}
                cropShape="round"
                showGrid={false}
                onCropChange={setCrop}
                onZoomChange={setZoom}
                onCropComplete={(_, pixels) => setAreaPixels(pixels)}
              />
            </div>
            <input
              type="range"
              min={1}
              max={3}
              step={0.01}
              value={zoom}
              aria-label="Zoom"
              onChange={(e) => setZoom(Number(e.target.value))}
            />
            {error && <p className="error">{error}</p>}
            <div className="row" style={{ justifyContent: "flex-end", marginTop: "0.75rem" }}>
              <button type="button" className="secondary" disabled={busy} onClick={closeCropper}>
                Cancel
              </button>
              <button type="button" disabled={busy || !areaPixels} onClick={onSave}>
                {busy ? "Saving…" : "Save photo"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
