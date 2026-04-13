import type { GetStaticPaths } from 'astro';
import citiesData from '~/data/cities.json';
import { getListingsForCity } from '~/lib/listings';
import { cityOgImage } from '~/utils/og-image';

export const getStaticPaths: GetStaticPaths = async () => {
  return (citiesData as any[]).map((city) => ({
    params: { stateSlug: city.stateSlug, citySlug: city.slug },
    props: { city },
  }));
};

export async function GET({ props }: { props: { city: any } }) {
  const { city } = props;
  const listings = getListingsForCity(city.slug);

  const png = await cityOgImage({
    city: city.city,
    state: city.stateAbbr || city.stateName,
    providerCount: listings.length,
  });

  return new Response(png, {
    headers: { 'Content-Type': 'image/png' },
  });
}
