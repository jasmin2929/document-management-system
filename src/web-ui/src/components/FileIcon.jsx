export default function FileIcon({ fileName }) {
  const extension = fileName?.includes('.') ? fileName.split('.').pop().slice(0, 4).toUpperCase() : 'FILE';
  return (
    <span className="file-icon" aria-hidden="true">
      {extension}
    </span>
  );
}
