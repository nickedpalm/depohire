// Utility to load all listing JSON files at build time
const listingModules = import.meta.glob<{ default: any[] }>('/src/data/listings/*.json', { eager: true });

export interface SentimentHighlight {
  text: string;
  sentiment: 'positive' | 'negative';
}

export interface Sentiment {
  label: 'positive' | 'mixed' | 'negative';
  score: number;
  keywords: string[];
  highlights: SentimentHighlight[];
  summary: string;
}

export interface Listing {
  slug: string;
  name: string;
  city: string;
  state: string;
  address: string;
  lat: number;
  lng: number;
  phone?: string;
  website?: string;
  email?: string;
  contact_form_url?: string;
  contact_method?: string;
  rating: number;
  review_count: number;
  description?: string;
  certifications?: string[];
  services?: string[];
  years_experience?: number;
  coverage_area?: string;
  equipment?: string[];
  demo_reel_url?: string;
  demo_reel_thumbnail?: string;
  photos?: { url: string; alt?: string }[];
  claimed: boolean;
  featured: boolean;
  source: string;
  scraped_at: string;
  sentiment?: Sentiment | null;
}

export function getAllListings(): Listing[] {
  const all: Listing[] = [];
  for (const mod of Object.values(listingModules)) {
    all.push(...(mod.default || []));
  }
  return all;
}

export function getListingsForCity(citySlug: string): Listing[] {
  const key = Object.keys(listingModules).find(k => k.endsWith(`/${citySlug}.json`));
  if (!key) return [];
  return listingModules[key]?.default || [];
}

export function getListingBySlug(slug: string): Listing | undefined {
  return getAllListings().find(l => l.slug === slug);
}

export function getListingCountByCity(): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const [path, mod] of Object.entries(listingModules)) {
    const slug = path.split('/').pop()?.replace('.json', '') || '';
    counts[slug] = (mod.default || []).length;
  }
  return counts;
}

export function getListingCountByState(): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const listing of getAllListings()) {
    counts[listing.state] = (counts[listing.state] || 0) + 1;
  }
  return counts;
}
