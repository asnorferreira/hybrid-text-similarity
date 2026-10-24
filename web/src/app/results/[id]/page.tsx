import { Workspace } from '../../../components/workspace';

export default async function ComparisonPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <Workspace initialId={id} />;
}
