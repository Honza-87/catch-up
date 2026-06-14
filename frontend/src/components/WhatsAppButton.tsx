export function WhatsAppButton({ e164 }: { e164: string | null }) {
  if (!e164) return null;
  const digits = e164.replace(/[^0-9]/g, "");
  return (
    <a href={`https://wa.me/${digits}`} target="_blank" rel="noreferrer">
      <button type="button">Message on WhatsApp</button>
    </a>
  );
}
