"""后端错误消息 i18n 回归：上传校验等英文文案必须按 Accept-Language 出中文。

背景：file_security / file_helpers 的 ValueError 与 ServiceResult.fail 的
英文字面量此前直接进响应体（AGENTS.md 遗留项「上传路径校验错误文案英文」）。
方案：消息源头保持英文 msgid，blueprint 出口统一 gettext；翻译目录在
backend/translations/zh_CN/LC_MESSAGES/messages.mo。
"""

import io

from flask_babel import gettext


def _post_pdf(client, url: str, filename: str = "a.exe", data: bytes = b"MZ\x90\x00"):
    return client.post(
        url,
        data={"file": (io.BytesIO(data), filename)},
        content_type="multipart/form-data",
        headers={"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"},
    )


class TestUploadValidationChinese:
    def test_extension_not_allowed_renders_zh(self, client):
        r = _post_pdf(client, "/api/v1/metadata-clean")
        assert r.status_code == 400
        assert "不允许" in r.get_json()["error"]

    def test_no_extension_renders_zh(self, client):
        r = _post_pdf(client, "/api/v1/metadata-clean", filename="README")
        assert r.status_code == 400
        msg = r.get_json()["error"]
        assert "扩展名" in msg and "README" not in msg

    def test_english_client_gets_english(self, client):
        r = client.post(
            "/api/v1/metadata-clean",
            data={"file": (io.BytesIO(b"MZ\x90\x00"), "a.exe")},
            content_type="multipart/form-data",
            headers={"Accept-Language": "en"},
        )
        assert r.status_code == 400
        assert "not allowed" in r.get_json()["error"]

    def test_magic_mismatch_renders_zh(self, client):
        # .pdf 扩展名合法但内容不是 %PDF 头 → magic number 拒绝
        r = _post_pdf(client, "/api/v1/metadata-clean", filename="evil.pdf", data=b"not a pdf at all")
        assert r.status_code == 400
        assert "格式" in r.get_json()["error"]


class TestServiceFailMessagesChinese:
    def test_no_file_provided_renders_zh(self, client):
        r = client.post(
            "/api/v1/metadata-clean",
            data={},
            content_type="multipart/form-data",
            headers={"Accept-Language": "zh-CN"},
        )
        assert r.status_code == 400
        assert "文件" in r.get_json()["error"]

    def test_excel_insufficient_files_renders_zh(self, client):
        pdf = b"%PDF-1.4\n%%EOF\n"
        r = client.post(
            "/api/v1/excel-merge",
            data={"files": [(io.BytesIO(pdf), "only-one.xlsx")]},
            content_type="multipart/form-data",
            headers={"Accept-Language": "zh-CN"},
        )
        # 单文件不满足合并条件：400 且消息已译
        assert r.status_code == 400
        body = r.get_json()
        assert body and ("至少" in body.get("error", "") or "至少" in body.get("msg", ""))


class TestCatalogIntegrity:
    def test_every_service_message_has_translation(self, app):
        """msgid 与目录一致性哨兵：目录里查不到的英文消息会让中文用户看到英文。

        不逐条断言（消息太多且合法地允许 en-only），只验证目录已加载且
        抽样几条核心上传消息确实翻成中文。
        """
        with app.test_request_context(headers={"Accept-Language": "zh-CN"}):
            assert gettext("File has no extension") != "File has no extension"
            assert gettext("No filename provided") != "No filename provided"
            assert gettext("Too many requests. Please try again later.") != (
                "Too many requests. Please try again later."
            )
