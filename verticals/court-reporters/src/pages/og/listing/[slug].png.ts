import type { GetStaticPaths } from 'astro';
import { getAllListings } from '~/lib/listings';
import citiesData from '~/data/cities.json';
import { listingOgImage } from '~/utils/og-image';

export const getStaticPaths: GetStaticPaths = async () => {
  const listings = getAllListings();
  return listings.map((listing) => ({
    params: { slug: listing.slug },
    props: { listing },
  }));
};

export async function GET({ props }: { props: { listing: any } }) {
  const { listing } = props;
  const cityInfo = (citiesData as any[]).find(
    (c) => c.slug === listing.city || c.city === listing.city
  );

  const png = await listingOgImage({
    name: listing.name,
    city: cityInfo?.city || listing.city,
    state: listing.state,
    rating: listing.rating,
    reviewCount: listing.review_count,
    certifications: listing.certifications,
  });

  return new Response(png, {
    headers: { 'Content-Type': 'image/png' },
  });
}
