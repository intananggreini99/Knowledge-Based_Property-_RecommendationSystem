import EvaluationPage from '@/components/EvaluationPage';

export const metadata = {
  title: 'Rumaku — Evaluasi Model Rekomendasi',
  description:
    'Ukur kualitas sistem rekomendasi properti dengan NDCG, Precision, Recall, F1, dan tingkat pemenuhan syarat.',
};

export default function Page() {
  return <EvaluationPage />;
}
