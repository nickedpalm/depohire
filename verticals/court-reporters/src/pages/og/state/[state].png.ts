import type { GetStaticPaths } from 'astro';
import citiesData from '~/data/cities.json';
import { getAllListings } from '~/lib/listings';
import { stateOgImage } from '~/utils/og-image';

export const getStaticPaths: GetStaticPaths = async () => {
  const cities = citiesData as any[];
  const stateMap = new Map<string, { stateName: string; stateSlug: string; cities: number; providers: number }>();

  const listings = getAllListings();
  for (const city of cities) {
    const key = city.stateSlug;
    if (!stateMap.has(key)) {
      stateMap.set(key, { stateName: city.stateName, stateSlug: key, cities: 0, providers: 0 });
    }
    stateMap.get(key)!.cities++;
  }

  for (const listing of listings) {
    const cityInfo = cities.find((c: any) => c.slug === listing.city || c.city === listing.city);
    if (cityInfo) {
      const entry = stateMap.get(cityInfo.stateSlug);
      if (entry) entry.providers++;
    }
  }

  return Array.from(stateMap.values()).map((s) => ({
    params: { state: s.stateSlug },
    props: { stateName: s.stateName, cityCount: s.cities, providerCount: s.providers },
  }));
};

export async function GET({ props }: { props: { stateName: string; cityCount: number; providerCount: number } }) {
  const png = await stateOgImage({
    state: props.stateName,
    cityCount: props.cityCount,
    providerCount: props.providerCount,
  });

  return new Response(png, {
    headers: { 'Content-Type': 'image/png' },
  });
}
