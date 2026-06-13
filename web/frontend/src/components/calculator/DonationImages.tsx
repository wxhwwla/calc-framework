import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import {
  DONATION_API_BASE,
  DONATION_IMAGE_SLOTS,
  donationImageUrl,
} from "../../constants/donation";

interface DonationImagesProps {
  maxWidth?: number;
}

type ResolvedSlot = { label: string; file: string | null };

const LABEL_I18N_MAP: Record<string, string> = {
  "微信赞赏码": "donation.weChatLabel",
  "爱发电": "donation.afdianLabel",
};

function resolveLabel(t: (key: string, options?: Record<string, unknown>) => string, label: string): string {
  const key = LABEL_I18N_MAP[label];
  return key ? t(key) : label;
}

/** 按槽位尝试候选文件名（微信 jpg / 爱发电 png 等可混用） */
export default function DonationImages({ maxWidth = 280 }: DonationImagesProps) {
  const { t } = useTranslation();
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
    let cancelled = false;
    fetch(`${DONATION_API_BASE}/manifest`)
      .then((r) => (r.ok ? r.json() : []))
      .then((items: { file: string; label: string }[]) => {
        if (cancelled) return;
        if (Array.isArray(items) && items.length > 0) {
          setSlots(
            DONATION_IMAGE_SLOTS.map((slot) => {
              const hit = items.find((it) => it.label === slot.label);
              return { label: slot.label, file: hit?.file ?? null };
            }),
          );
          return;
        }
        DONATION_IMAGE_SLOTS.forEach((_slot, i) => probeSlot(i, 0));
      })
      .catch(() => {
        if (!cancelled) DONATION_IMAGE_SLOTS.forEach((_slot, i) => probeSlot(i, 0));
      });
    return () => {
      cancelled = true;
    };
  }, [probeSlot]);

  const visible = slots.filter((s) => s.file);

  return (
    <Box sx={{ py: 1 }}>
      {visible.length === 0 && (
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
          {t("donation.noQrConfigured")}
        </Typography>
      )}
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, justifyContent: "center" }}>
        {slots.map(({ label, file }) =>
          file ? (
            <Box key={label} sx={{ textAlign: "center" }}>
              <Box
                component="img"
                src={donationImageUrl(file)}
                alt={resolveLabel(t, label)}
                sx={{ maxWidth, width: "100%", borderRadius: 1 }}
              />
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 0.5 }}>
                {resolveLabel(t, label)}
              </Typography>
            </Box>
          ) : null,
        )}
      </Box>
    </Box>
  );
}
