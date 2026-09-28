import { Link } from 'react-router-dom';
import { formatDate, formatFileSize } from '../utils/format';

export default function DocumentList({ documents }) {
  if (documents.length === 0) {
    return <p>No documents found.</p>;
  }

  return (
    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Category</th>
          <th>Status</th>
          <th>Size</th>
          <th>Uploaded</th>
        </tr>
      </thead>
      <tbody>
        {documents.map((document) => (
          <tr key={document.id}>
            <td>
              <Link to={`/documents/${document.id}`}>{document.title}</Link>
            </td>
            <td>{document.category?.name ?? '—'}</td>
            <td>{document.status}</td>
            <td>{formatFileSize(document.fileSize)}</td>
            <td>{formatDate(document.uploadDate)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
