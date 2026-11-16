<template>
  <div class="card bg-surface border-default">
    <div class="grid gap-6">
      <UFormGroup :label="$t('meetingMinutes.meetName')" :hint="$t('meetingMinutes.meetNameHint')">
        <UInput
          v-model="meetName"
          size="lg"
          :placeholder="$t('meetingMinutes.meetNamePlaceholder')"
          :disabled="generating"
        />
      </UFormGroup>

      <UFormGroup :label="$t('meetingMinutes.body')" :hint="$t('meetingMinutes.bodyHint')">
        <UTextarea
          v-model="body"
          :rows="12"
          :autoresize="true"
          :placeholder="$t('meetingMinutes.bodyPlaceholder')"
          :disabled="generating"
        />
      </UFormGroup>

      <UFormGroup :label="$t('meetingMinutes.attachments')" :hint="$t('meetingMinutes.attachmentsHint')">
        <UTextarea
          v-model="attachments"
          :rows="3"
          :autoresize="true"
          :placeholder="$t('meetingMinutes.attachmentsPlaceholder')"
          :disabled="generating"
        />
      </UFormGroup>

      <div class="grid gap-4 sm:grid-cols-3">
        <UFormGroup
          v-for="field in ROSTER_FIELDS"
          :key="field.key"
          :label="$t(field.labelKey)"
          :hint="$t('meetingMinutes.rosterHint')"
        >
          <UTextarea
            v-model="rosters[field.key]"
            :rows="3"
            :autoresize="true"
            :placeholder="$t('meetingMinutes.rosterPlaceholder')"
            :disabled="generating"
          />
        </UFormGroup>
      </div>

      <UFormGroup :label="$t('meetingMinutes.colophon.cc')" :hint="$t('meetingMinutes.colophon.ccHint')">
        <UTextarea
          v-model="ccOrgs"
          :rows="2"
          :autoresize="true"
          :placeholder="$t('meetingMinutes.colophon.ccPlaceholder')"
          :disabled="generating"
        />
      </UFormGroup>

      <div class="grid gap-4 sm:grid-cols-2">
        <UFormGroup :label="$t('meetingMinutes.colophon.printOrg')">
          <UInput
            v-model="printOrg"
            :placeholder="$t('meetingMinutes.colophon.printOrgPlaceholder')"
            :disabled="generating"
          />
        </UFormGroup>
        <UFormGroup :label="$t('meetingMinutes.colophon.printDate')">
          <UInput v-model="printDate" type="date" :disabled="generating" />
        </UFormGroup>
      </div>

      <p class="text-xs text-tertiary">{{ $t("meetingMinutes.colophon.hint") }}</p>

      <p v-if="error" class="text-sm text-red-600" role="alert">{{ error }}</p>

      <UButton color="primary" size="lg" :loading="generating" :disabled="!canGenerate" @click="generate">
        <UIcon name="i-heroicons-document-arrow-down" class="w-4 h-4 mr-1.5" />
        {{ generating ? $t("common.processing") : $t("meetingMinutes.generate") }}
      </UButton>

      <p class="text-xs text-tertiary">{{ $t("meetingMinutes.levels") }}</p>
      <p class="text-xs text-tertiary">{{ $t("meetingMinutes.note") }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from "axios";
import { filenameFromDisposition } from "~/utils/contentDisposition";
import { parseRoster, type RosterPerson } from "~/utils/roster";

const { t } = useI18n();
const { extractError, showError } = useApiError();
const { downloadBlob } = useDownload();

// 顺序按 10.3 的行款：出席 → 请假 → 列席；key 与后端字段名一致。
const ROSTER_FIELDS = [
  { key: "attendees", labelKey: "meetingMinutes.attendees" },
  { key: "leave", labelKey: "meetingMinutes.leave" },
  { key: "witness", labelKey: "meetingMinutes.witness" },
] as const;

type RosterKey = (typeof ROSTER_FIELDS)[number]["key"];

const meetName = ref("");
const body = ref("");
const attachments = ref("");
const ccOrgs = ref("");
const printOrg = ref("");
const printDate = ref("");
const generating = ref(false);
const rosters = reactive<Record<RosterKey, string>>({ attendees: "", leave: "", witness: "" });

// 每行一个自然段：textarea 里回车就是分段，不做任何文本解析（D7）。
const lines = (text: string) => text.split("\n").map((line) => line.trim()).filter(Boolean);
const paragraphs = computed(() => lines(body.value));
const canGenerate = computed(() => meetName.value.trim().length > 0 && paragraphs.value.length > 0);

function rosterPayload(): Record<RosterKey, RosterPerson[]> {
  return Object.fromEntries(
    ROSTER_FIELDS.map(({ key }) => [key, parseRoster(rosters[key])]),
  ) as Record<RosterKey, RosterPerson[]>;
}

const error = ref("");

async function generate() {
  if (!canGenerate.value) return;
  error.value = "";
  generating.value = true;
  try {
    const resp = await axios.post(
      "/api/v1/meeting-minutes",
      {
        meet_name: meetName.value.trim(),
        paragraphs: paragraphs.value,
        attachments: lines(attachments.value),
        cc_orgs: lines(ccOrgs.value),
        print_org: printOrg.value.trim(),
        print_date: printDate.value || null,
        ...rosterPayload(),
      },
      { responseType: "blob" },
    );
    downloadBlob(
      resp.data,
      filenameFromDisposition(resp.headers["content-disposition"], `${t("meetingMinutes.title")}.docx`),
      t("common.success"),
    );
  } catch (e: any) {
    const status = e?.response?.status;
    // 422/400 是用户能自己改好的字段问题：内联展示，不弹覆盖表单的 toast。
    if (status === 422 || status === 400) {
      error.value = await extractError(e);
    } else {
      showError(e);
    }
  } finally {
    generating.value = false;
  }
}
</script>
