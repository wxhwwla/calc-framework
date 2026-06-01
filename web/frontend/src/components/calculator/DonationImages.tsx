import { useCallback, useEffect, useState } from "react";
import { Box, Typography } from "@mui/material";
import {
  DONATION_IMAGE_SLOTS,
  donationImageUrl,
} from "../../constants/donation";

interface DonationImagesProps {
  maxWidth?: number;
}

type ResolvedSlot = { label: string; file: string | null };

/** 按槽位尝试候选文件名（微信 jpg / 爱发电 png 等可混用） */
export default function DonationImages({ maxWidth = 280 }: DonationImagesProps) {
  const [slots, setSlots] = useState<ResolvedSlot[]>(() =>
    DONATION_IMAGE_SLOTS.map((s) => ({ label: s.label, file: null })),
  );

  const probeSlot = useCallback((slotIndex: number, candidateIndex: number) => {
    const slot = DONATION_IMAGE_SLOTS[slotIndex];
    const file = slot.candidates[candidateIndex];
    if (!file) {
      setSlots((prev) => {
        const next = [...prev];
        next[slotIndex] = { label: slot.label, file: null };
        return next;
      });
      return;
    }
    const img = new Image();
    img.onload = () => {
      setSlots((prev) => {
        const next = [...prev];
        next[slotIndex] = { label: slot.label, file };
        return next;
      });
    };
    img.onerror = () => probeSlot(slotIndex, candidateIndex + 1);
    img.src = donationImageUrl(file);
  }, []);

  useEffect(() => {
    DONATION_IMAGE_SLOTS.forEach((_slot, i) => probeSlot(i, 0));
  }, [probeSlot]);

  const visible = slots.filter((s) => s.file);

  return (
    <Box sx={{ py: 1 }}>
      {visible.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
          暂未配置捐赠二维码（微信 donation_qr.jpg / 爱发电 afdian_qr.png 等，放入
          resources/donation/）
        </Typography>
      )}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, justifyContent: "center" }}>
        {slots.map(({ label, file }) =>
          file ? (
            <Box key={label} sx={{ textAlign: "center" }}>
              <Box
                component="img"
                src={donationImageUrl(file)}
                alt={label}
                sx={{ maxWidth, width: "100%", borderRadius: 1 }}
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                {label}
              </Typography>
            </Box>
          ) : null,
        )}
      </Box>
    </Box>
  );
}
