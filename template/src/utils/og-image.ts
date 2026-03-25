/**
 * Build-time OG image generation using satori + sharp.
 * Generates 1200×630 PNG images for social sharing.
 */
import satori from 'satori';
import sharp from 'sharp';
import fs from 'node:fs';
import path from 'node:path';
import config from '~/config';

const interRegular = fs.readFileSync(
  path.resolve('src/assets/fonts/Inter-Regular.ttf')
);
const interBold = fs.readFileSync(
  path.resolve('src/assets/fonts/Inter-Bold.ttf')
);

const WIDTH = 1200;
const HEIGHT = 630;

const fonts = [
  { name: 'Inter', data: interRegular, weight: 400 as const, style: 'normal' as const },
  { name: 'Inter', data: interBold, weight: 700 as const, style: 'normal' as const },
];

async function renderOgImage(jsx: any): Promise<Buffer> {
  const svg = await satori(jsx, { width: WIDTH, height: HEIGHT, fonts });
  return await sharp(Buffer.from(svg)).png({ quality: 85 }).toBuffer();
}

/** Listing detail page OG image */
export async function listingOgImage(opts: {
  name: string;
  city: string;
  state: string;
  rating?: number;
  reviewCount?: number;
  certifications?: string[];
}): Promise<Buffer> {
  const stars = opts.rating ? '★'.repeat(Math.round(opts.rating)) + '☆'.repeat(5 - Math.round(opts.rating)) : '';

  const jsx = {
    type: 'div',
    props: {
      style: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #0f2744 0%, #1e3a5f 50%, #2a4a6b 100%)',
        padding: '60px',
        fontFamily: 'Inter',
        color: '#ffffff',
      },
      children: [
        {
          type: 'div',
          props: {
            style: { display: 'flex', flexDirection: 'column', gap: '16px' },
            children: [
              {
                type: 'div',
                props: {
                  style: {
                    fontSize: '18px',
                    fontWeight: 700,
                    color: '#60a5fa',
                    textTransform: 'uppercase',
                    letterSpacing: '2px',
                  },
                  children: config.brandName,
                },
              },
              {
                type: 'div',
                props: {
                  style: {
                    fontSize: opts.name.length > 30 ? '42px' : '52px',
                    fontWeight: 700,
                    lineHeight: 1.1,
                    maxWidth: '900px',
                  },
                  children: opts.name,
                },
              },
              {
                type: 'div',
                props: {
                  style: {
                    fontSize: '26px',
                    color: '#94a3b8',
                    marginTop: '4px',
                  },
                  children: `Deposition Videographer in ${opts.city}, ${opts.state}`,
                },
              },
            ],
          },
        },
        {
          type: 'div',
          props: {
            style: {
              display: 'flex',
              alignItems: 'center',
              gap: '32px',
            },
            children: [
              ...(stars
                ? [
                    {
                      type: 'div',
                      props: {
                        style: { display: 'flex', alignItems: 'center', gap: '8px' },
                        children: [
                          {
                            type: 'div',
                            props: {
                              style: { fontSize: '28px', color: '#fbbf24' },
                              children: stars,
                            },
                          },
                          {
                            type: 'div',
                            props: {
                              style: { fontSize: '20px', color: '#94a3b8' },
                              children: opts.reviewCount ? `(${opts.reviewCount} reviews)` : '',
                            },
                          },
                        ],
                      },
                    },
                  ]
                : []),
              ...(opts.certifications?.length
                ? [
                    {
                      type: 'div',
                      props: {
                        style: {
                          display: 'flex',
                          gap: '8px',
                        },
                        children: opts.certifications.slice(0, 3).map((cert) => ({
                          type: 'div',
                          props: {
                            style: {
                              background: 'rgba(96, 165, 250, 0.15)',
                              border: '1px solid rgba(96, 165, 250, 0.3)',
                              borderRadius: '6px',
                              padding: '6px 14px',
                              fontSize: '16px',
                              color: '#93c5fd',
                            },
                            children: cert,
                          },
                        })),
                      },
                    },
                  ]
                : []),
            ],
          },
        },
      ],
    },
  };

  return renderOgImage(jsx);
}

/** City page OG image */
export async function cityOgImage(opts: {
  city: string;
  state: string;
  providerCount: number;
}): Promise<Buffer> {
  const jsx = {
    type: 'div',
    props: {
      style: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #0f2744 0%, #1e3a5f 50%, #2a4a6b 100%)',
        padding: '60px',
        fontFamily: 'Inter',
        color: '#ffffff',
        textAlign: 'center',
      },
      children: [
        {
          type: 'div',
          props: {
            style: {
              fontSize: '18px',
              fontWeight: 700,
              color: '#60a5fa',
              textTransform: 'uppercase',
              letterSpacing: '2px',
              marginBottom: '20px',
            },
            children: config.brandName,
          },
        },
        {
          type: 'div',
          props: {
            style: {
              fontSize: '56px',
              fontWeight: 700,
              lineHeight: 1.1,
              marginBottom: '16px',
            },
            children: `${opts.city}, ${opts.state}`,
          },
        },
        {
          type: 'div',
          props: {
            style: {
              fontSize: '28px',
              color: '#94a3b8',
              marginBottom: '32px',
            },
            children: 'Deposition Videographers',
          },
        },
        {
          type: 'div',
          props: {
            style: {
              background: 'rgba(96, 165, 250, 0.15)',
              border: '1px solid rgba(96, 165, 250, 0.3)',
              borderRadius: '12px',
              padding: '12px 32px',
              fontSize: '22px',
              color: '#93c5fd',
            },
            children: `${opts.providerCount} Curated Provider${opts.providerCount !== 1 ? 's' : ''}`,
          },
        },
      ],
    },
  };

  return renderOgImage(jsx);
}

/** Blog post OG image */
export async function blogOgImage(opts: {
  title: string;
  category?: string;
}): Promise<Buffer> {
  const jsx = {
    type: 'div',
    props: {
      style: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0f2744 0%, #1e3a5f 50%, #2a4a6b 100%)',
        padding: '60px 80px',
        fontFamily: 'Inter',
        color: '#ffffff',
      },
      children: [
        {
          type: 'div',
          props: {
            style: {
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
              marginBottom: '28px',
            },
            children: [
              {
                type: 'div',
                props: {
                  style: {
                    fontSize: '18px',
                    fontWeight: 700,
                    color: '#60a5fa',
                    textTransform: 'uppercase',
                    letterSpacing: '2px',
                  },
                  children: config.brandName,
                },
              },
              ...(opts.category
                ? [
                    {
                      type: 'div',
                      props: {
                        style: { fontSize: '18px', color: '#475569' },
                        children: '·',
                      },
                    },
                    {
                      type: 'div',
                      props: {
                        style: { fontSize: '18px', color: '#94a3b8' },
                        children: opts.category,
                      },
                    },
                  ]
                : []),
            ],
          },
        },
        {
          type: 'div',
          props: {
            style: {
              fontSize: opts.title.length > 60 ? '38px' : '48px',
              fontWeight: 700,
              lineHeight: 1.2,
              maxWidth: '1000px',
            },
            children: opts.title,
          },
        },
      ],
    },
  };

  return renderOgImage(jsx);
}

/** State page OG image */
export async function stateOgImage(opts: {
  state: string;
  cityCount: number;
  providerCount: number;
}): Promise<Buffer> {
  const jsx = {
    type: 'div',
    props: {
      style: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        background: 'linear-gradient(135deg, #0f2744 0%, #1e3a5f 50%, #2a4a6b 100%)',
        padding: '60px',
        fontFamily: 'Inter',
        color: '#ffffff',
        textAlign: 'center',
      },
      children: [
        {
          type: 'div',
          props: {
            style: {
              fontSize: '18px',
              fontWeight: 700,
              color: '#60a5fa',
              textTransform: 'uppercase',
              letterSpacing: '2px',
              marginBottom: '20px',
            },
            children: config.brandName,
          },
        },
        {
          type: 'div',
          props: {
            style: {
              fontSize: '56px',
              fontWeight: 700,
              lineHeight: 1.1,
              marginBottom: '16px',
            },
            children: opts.state,
          },
        },
        {
          type: 'div',
          props: {
            style: {
              fontSize: '28px',
              color: '#94a3b8',
              marginBottom: '32px',
            },
            children: 'Deposition Videographers',
          },
        },
        {
          type: 'div',
          props: {
            style: {
              display: 'flex',
              gap: '24px',
            },
            children: [
              {
                type: 'div',
                props: {
                  style: {
                    background: 'rgba(96, 165, 250, 0.15)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    borderRadius: '12px',
                    padding: '12px 32px',
                    fontSize: '22px',
                    color: '#93c5fd',
                  },
                  children: `${opts.cityCount} Cit${opts.cityCount !== 1 ? 'ies' : 'y'}`,
                },
              },
              {
                type: 'div',
                props: {
                  style: {
                    background: 'rgba(96, 165, 250, 0.15)',
                    border: '1px solid rgba(96, 165, 250, 0.3)',
                    borderRadius: '12px',
                    padding: '12px 32px',
                    fontSize: '22px',
                    color: '#93c5fd',
                  },
                  children: `${opts.providerCount} Provider${opts.providerCount !== 1 ? 's' : ''}`,
                },
              },
            ],
          },
        },
      ],
    },
  };

  return renderOgImage(jsx);
}
