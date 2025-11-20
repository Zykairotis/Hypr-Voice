import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Audio Mixer - Hypr-Voice',
  description: 'Professional audio monitoring and mixing interface',
};

export default function AudioMixerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
