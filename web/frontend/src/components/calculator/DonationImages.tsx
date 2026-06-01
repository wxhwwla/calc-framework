import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { DONATION_IMAGES, donationImageUrl } from "../../constants/donation";

interface DonationImagesProps {
  maxWidth?: number;
}

/** 捐赠二维码展示（文件缺失时自动隐藏对应项） */
export default function DonationImages({ maxWidth = 280 }: DonationImagesProps) {
  const [hidden, setHidden] = useState<Set<string>>(() => new Set());

  const hide = (file: string) => {
    setHidden((prev) => {
      if (prev.has(file)) return prev;
      const next = new Set(prev);
      next.add(file);
      return next;
    });
  };

  const visibleCount = DONATION_IMAGES.length - hidden.size;

  return (
    <Box sx={{ py: 1 }}>
      {visibleCount === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
          暂未配置捐赠二维码（请将 donation_qr.png、afdian_qr.png 放入 resources/donation/）
        </Typography>
      )}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, justifyContent: "center" }}>
        {DONATION_IMAGES.map(({ file, label }) => (
          <Box
            key={file}
            sx={{ textAlign: "center", display: hidden.has(file) ? "none" : "block" }}
          >
            <Box
              component="img"
              src={donationImageUrl(file)}
              alt={label}
              sx={{ maxWidth, width: "100%", borderRadius: 1 }}
              onError={() => hide(file)}
            />
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
              {label}
            </Typography>
          </Box>
        ))}
      </Box>
    </Box>
  );
}
