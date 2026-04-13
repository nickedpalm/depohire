import type { GetStaticPaths } from 'astro';
import { getCollection } from 'astro:content';
import { blogOgImage } from '~/utils/og-image';

export const getStaticPaths: GetStaticPaths = async () => {
  const posts = await getCollection('blog');
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { title: post.data.title, category: post.data.category || post.data.hub || '' },
  }));
};

export async function GET({ props }: { props: { title: string; category: string } }) {
  const png = await blogOgImage({
    title: props.title,
    category: props.category,
  });

  return new Response(png, {
    headers: { 'Content-Type': 'image/png' },
  });
}
