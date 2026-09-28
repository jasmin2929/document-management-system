import { useParams } from 'react-router-dom';

export default function DocumentDetail() {
  const { id } = useParams();

  return (
    <section>
      <h1>Document #{id}</h1>
      <p>Document details coming soon.</p>
    </section>
  );
}
