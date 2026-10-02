import { Link } from 'react-router-dom';
import { formatDate, formatFileSize } from '../utils/format';
import FileIcon from './FileIcon';
import StatusBadge from './StatusBadge';

export default function DocumentList({ documents, emptyMessage }) {
  return (
    <div className="card doc-table">
      <div className="doc-row doc-row--head" role="presentation">
        <div>Title</div>
        <div>Category</div>
        <div>Status</div>
        <div className="text-right">Size</div>
        <div>Uploaded</div>
      </div>

      {documents.length === 0 ? (
        <div className="empty-state">{emptyMessage}</div>
      ) : (
        documents.map((document) => (
          <Link key={document.id} to={`/documents/${document.id}`} className="doc-row">
            <div className="doc-row__title">
              <FileIcon fileName={document.originalFileName} />
              <span className="doc-row__title-text" title={document.title}>
                {document.title}
              </span>
            </div>
            <div className={`doc-row__category${document.category ? '' : ' doc-row__none'}`}>
              {document.category?.name ?? '—'}
            </div>
            <div className="doc-row__status">
              <StatusBadge status={document.status} />
            </div>
            <div className="doc-row__size">{formatFileSize(document.fileSize)}</div>
            <div className="doc-row__date">{formatDate(document.uploadDate)}</div>
          </Link>
        ))
      )}
    </div>
  );
}
