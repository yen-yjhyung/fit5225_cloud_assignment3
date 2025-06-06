This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

## S3 File Structure
```
s3://bird-bucket/
│
├── images/
│   ├── 230a6c42-1757-4bbe-bf17-0ac1fb7ee252.png
│   └── d6bd1fde-d347-4a69-b6a2-8792ac07e31e.jpg
│
├── videos/
│   ├── 9a8bbc1d-0c10-4e0e-8dfb-6d113fc62244.mp4
│   └── 33486101-7ec4-483c-b981-2e64fbf1a8b8.avi
│
├── audios/
│   ├── fd89b09f-4721-49df-8eb1-17b36ae0aac4.mp3
│   └── 3602dc50-e500-4a6b-842d-6ddf72bdb035.mp3
│
└── thumbnails/
    ├── 230a6c42-1757-4bbe-bf17-0ac1fb7ee252_thumb.jpg  # same uuid from image file with 'thumb' surffix
    └── d6bd1fde-d347-4a69-b6a2-8792ac07e31e_thumb.jpg
```

## DynamoDB Document Format
```json
{
  "id": {
    "S": "230a6c42-1757-4bbe-bf17-0ac1fb7ee252"
  },
  "key": {
    "S": "images/230a6c42-1757-4bbe-bf17-0ac1fb7ee252.png"
  },
  "bucket": {
    "S": "birdtag-upload-bucket"
  },
  "size": {
    "N": "82209"
  },
  "thumbnailKey": {
    "S": "thumbnails/230a6c42-1757-4bbe-bf17-0ac1fb7ee252_thumb.jpeg"
  },
  "type": {
    "S": "image"
  },
  "format": {
    "S": "png"
  },
  "tags": {
    "L": [
      {
        "M": {
          "count": {
            "N": "2"
          },
          "name": {
            "S": "crow"
          }
        }
      },
      {
        "M": {
          "count": {
            "N": "1"
          },
          "name": {
            "S": "pigeon"
          }
        }
      }
    ]
  }
}
```
