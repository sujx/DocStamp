<template>
  <div class="pt-3">
    <h2 class="text-2xl font-bold mb-1 text-balance">{{ $t("watermark.title") }}</h2>
    <p class="text-sm mb-5 text-pretty text-secondary" >{{ $t("watermark.description") }}</p>

    <FileUploader
      ref="uploader"
      accept=".pdf,.docx"
      icon="i-heroicons-document-text"
      @file-selected="selectedFile = $event"
      @reset="selectedFile = null"
    />

    <div v-if="selectedFile" class="p-4 mt-4 rounded-lg bg-surface" >
      <!-- Type toggle -->
      <div class="flex gap-4 mb-4">
        <label class="flex items-center gap-1.5 text-sm cursor-pointer text-primary" >
          <input type="radio" v-model="params.watermark_type" value="text" class="accent-green-700" />
          {{ $t("watermark.typeText") }}
        </label>
        <label class="flex items-center gap-1.5 text-sm cursor-pointer text-primary" >
          <input type="radio" v-model="params.watermark_type" value="image" class="accent-green-700" />
          {{ $t("watermark.typeImage") }}
        </label>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <template v-if="params.watermark_type === 'text'">
          <UFormGroup :label="$t('watermark.text')">
            <UInput v-model="params.text" :placeholder="$t('watermark.textPlaceholder')" />
          </UFormGroup>
          <UFormGroup :label="$t('watermark.font')">
            <USelect v-model="params.font" :options="fontOptions" />
          </UFormGroup>
          <UFormGroup :label="$t('watermark.fontSize')">
            <UInput v-model.number="params.font_size" type="number" :min="8" :max="200" />
          </UFormGroup>
          <UFormGroup :label="$t('watermark.color')">
            <UInput v-model="params.color" type="color" class="h-9 w-16 p-1" />
          </UFormGroup>
        </template>
        <template v-else>
          <UFormGroup :label="$t('watermark.imageFile')">
            <label>
              <UButton color="primary" variant="soft" as="span" size="sm">
                <UIcon name="i-heroicons-photo" class="w-4 h-4 mr-1" />
                {{ watermarkImageName || $t("watermark.imageFile") }}
              </UButton>
              <input type="file" accept=".png,.jpg,.jpeg" class="hidden" @change="onImageSelected" />
            </label>
          </UFormGroup>
          <UFormGroup :label="$t('watermark.imageSize')">
            <UInput v-model.number="params.image_size" type="number" :min="20" :max="500" />
          </UFormGroup>
        </template>

        <UFormGroup :label="$t('watermark.opacity')">
          <input type="range" min="0" max="1" step="0.05" v-model.number="params.opacity" class="w-full accent-green-700" />
          <span class="text-xs text-pretty text-tertiary" >{{ params.opacity }}</span>
        </UFormGroup>

        <UFormGroup :label="$t('watermark.rotation')">
          <input type="range" min="-180" max="180" step="5" v-model.number="params.rotation" class="w-full accent-green-700" />
          <span class="text-xs text-pretty text-tertiary" >{{ params.rotation }}&deg;</span>
        </UFormGroup>

        <UFormGroup :label="$t('watermark.position')" class="md:col-span-2">
          <div class="flex gap-4">
            <label class="flex items-center gap-1.5 text-sm cursor-pointer text-primary" >
              <input type="radio" v-model="params.position" value="tile" class="accent-green-700" />
              {{ $t("watermark.positionTile") }}
            </label>
            <label class="flex items-center gap-1.5 text-sm cursor-pointer text-primary" >
              <input type="radio" v-model="params.position" value="center" class="accent-green-700" />
              {{ $t("watermark.positionCenter") }}
            </label>
          </div>
        </UFormGroup>

        <template v-if="params.position === 'tile'">
          <UFormGroup :label="$t('watermark.spacingX')">
            <UInput v-model.number="params.spacing_x" type="number" :min="50" :max="500" />
          </UFormGroup>
          <UFormGroup :label="$t('watermark.spacingY')">
            <UInput v-model.number="params.spacing_y" type="number" :min="50" :max="500" />
          </UFormGroup>
        </template>
      </div>

      <!-- Preview canvas -->
      <div class="mb-4">
        <p class="text-xs mb-2 text-tertiary" >{{ $t("watermark.preview") }}</p>
        <canvas ref="previewCanvas" class="w-full rounded border" style="height:280px; border-color:#e8e6d8;"></canvas>
      </div>

      <UButton color="primary" :loading="isProcessing" block @click="addWatermark">
        {{ $t("watermark.add") }}
      </UButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import FileUploader from "./FileUploader.vue";

const { t } = useI18n();
const { downloadBlob, showError } = useDownload();

const selectedFile = ref<File | null>(null);
const watermarkImage = ref<File | null>(null);
const watermarkImageName = ref("");
const watermarkImageDataUrl = ref("");
const isProcessing = ref(false);
const previewCanvas = ref<HTMLCanvasElement | null>(null);

const params = reactive({
  watermark_type: "text",
  text: "",
  font: "Helvetica",
  font_size: 48,
  color: "#D0D0D0",
  image_size: 150,
  opacity: 0.3,
  rotation: -45,
  position: "tile",
  spacing_x: 200,
  spacing_y: 200,
});

const fontOptions = ["Helvetica", "Times-Roman", "Courier", "SimSun", "SimHei"].map(f => ({ value: f, label: f }));

function onImageSelected(evt: Event) {
  const f = (evt.target as HTMLInputElement).files?.[0];
  if (!f) return;
  watermarkImage.value = f;
  watermarkImageName.value = f.name;
  const reader = new FileReader();
  reader.onload = (e) => { watermarkImageDataUrl.value = e.target!.result as string; drawPreview(); };
  reader.readAsDataURL(f);
}

function drawPreview() {
  const canvas = previewCanvas.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d")!;
  canvas.width = 400;
  canvas.height = 280;
  ctx.fillStyle = "#f9f7e8";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  if (params.watermark_type === "text" && params.text) {
    ctx.save();
    ctx.globalAlpha = params.opacity;
    ctx.fillStyle = params.color;
    if (params.position === "center") {
      ctx.translate(canvas.width / 2, canvas.height / 2);
      ctx.rotate((params.rotation * Math.PI) / 180);
      ctx.font = `${params.font_size}px ${params.font}`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(params.text, 0, 0);
    } else {
      ctx.rotate((params.rotation * Math.PI) / 180);
      ctx.font = `${params.font_size}px ${params.font}`;
      for (let y = -canvas.height; y < canvas.height * 2; y += params.spacing_y) {
        for (let x = -canvas.width; x < canvas.width * 2; x += params.spacing_x) {
          ctx.fillText(params.text, x, y);
        }
      }
    }
    ctx.restore();
  } else if (params.watermark_type === "image" && watermarkImageDataUrl.value) {
    const img = new Image();
    img.onload = () => {
      ctx.save();
      ctx.globalAlpha = params.opacity;
      const size = params.image_size;
      if (params.position === "center") {
        ctx.drawImage(img, (canvas.width - size) / 2, (canvas.height - size) / 2, size, size);
      } else {
        for (let y = 0; y < canvas.height + params.spacing_y; y += params.spacing_y) {
          for (let x = 0; x < canvas.width + params.spacing_x; x += params.spacing_x) {
            ctx.drawImage(img, x, y, size, size);
          }
        }
      }
      ctx.restore();
    };
    img.src = watermarkImageDataUrl.value;
  }
}

watch(params, () => nextTick(drawPreview), { deep: true });

async function addWatermark() {
  if (!selectedFile.value) return;
  if (params.watermark_type === "text" && !params.text) {
    useToast().add({ title: t("watermark.textRequired"), color: "warning" });
    return;
  }
  if (params.watermark_type === "image" && !watermarkImage.value) {
    useToast().add({ title: t("watermark.imageRequired"), color: "warning" });
    return;
  }
  isProcessing.value = true;
  try {
    const fd = new FormData();
    fd.append("file", selectedFile.value);
    fd.append("params", JSON.stringify({ ...params }));
    if (watermarkImage.value) fd.append("watermark_image", watermarkImage.value);
    const resp = await axios.post("/api/v1/watermark", fd, { responseType: "blob" });
    downloadBlob(resp.data, `watermarked_${selectedFile.value.name}`, t("common.success"));
  } catch (e) { showError(e); }
  finally { isProcessing.value = false; }
}
</script>
