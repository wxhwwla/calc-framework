/** 与 utils/donation_assets.py DONATION_IMAGE_SLOTS 保持一致 */
export const DONATION_IMAGE_SLOTS = [
  {
    label: "微信赞赏码",
    candidates: [
      "donation_qr.jpg",
      "donation_qr.jpeg",
      "donation_q.jpg",
      "donation_qr.png",
      "donation_qr.webp",
    ],
  },
  {
    label: "爱发电",
    candidates: ["afdian_qr.png", "afdian_qr.jpg", "afdian_qr.jpeg", "afdian_qr.webp"],
  },
] as const;

export const DONATION_TEXT =
  "感谢使用！如果觉得有用，欢迎通过微信赞赏或爱发电支持开发者。\n\n" +
  "捐赠纯属自愿，不构成购买软件的对价，不授予商业使用授权。";

export const DONATION_API_BASE = "/api/donation";

export function donationImageUrl(file: string): string {
  return `${DONATION_API_BASE}/${encodeURIComponent(file)}`;
}
