/** 与 resources/donation/ 及后端 /api/donation/ 静态目录一致 */
export const DONATION_IMAGES = [
  { file: "donation_qr.png", label: "微信赞赏码" },
  { file: "afdian_qr.png", label: "爱发电" },
] as const;

export const DONATION_API_BASE = "/api/donation";

export function donationImageUrl(file: string): string {
  return `${DONATION_API_BASE}/${encodeURIComponent(file)}`;
}
