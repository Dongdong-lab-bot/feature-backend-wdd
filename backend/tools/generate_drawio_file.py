# 文件路径：tools/generate_drawio_file.py
import os
import sys
import html

# 1. 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
docs_dir = os.path.join(project_root, "docs")
md_path = os.path.join(docs_dir, "er_diagram.md")
drawio_path = os.path.join(docs_dir, "er_diagram.drawio")

def generate_drawio():
    # 2. 读取刚才生成的 Markdown 文件
    if not os.path.exists(md_path):
        print(f"❌ 错误：找不到 {md_path}")
        print("   请先运行 python tools/generate_er.py 生成 Markdown 文件！")
        return

    print(f"📖 正在读取: {md_path}")
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 3. 清洗代码（去掉 markdown 的 ```mermaid 包裹）
    # 这样 draw.io 里的插件才能正确识别
    mermaid_code = content.replace("```mermaid", "").replace("```", "").strip()

    if not mermaid_code:
        print("❌ 错误：ER 图内容为空，请检查 er_diagram.md")
        return

    # 4. 构造 draw.io 的 XML
    escaped_code = html.escape(mermaid_code)
    
    drawio_xml = f"""<mxfile host="Electron" modified="2023-10-01T00:00:00.000Z" agent="5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) draw.io/21.6.8 Chrome/114.0.5735.289 Electron/25.5.0 Safari/537.36" etag="12345" version="21.6.8" type="device">
      <diagram id="Page-1" name="Page-1">
        <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
          <root>
            <mxCell id="0" />
            <mxCell id="1" parent="0" />
            <mxCell id="2" value="&lt;h1&gt;ER Diagram Source&lt;/h1&gt;&lt;p&gt;这是自动同步的 Mermaid 源码，请点击 Insert -&gt; Advanced -&gt; Mermaid 重新渲染&lt;/p&gt;&lt;pre&gt;{escaped_code}&lt;/pre&gt;" style="text;html=1;strokeColor=none;fillColor=none;spacing=5;spacingTop=-20;whiteSpace=wrap;overflow=hidden;rounded=0;" vertex="1" parent="1">
              <mxGeometry x="40" y="40" width="600" height="500" as="geometry" />
            </mxCell>
          </root>
        </mxGraphModel>
      </diagram>
    </mxfile>
    """

    # 5. 写入文件（覆盖旧的）
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(drawio_xml)

    print(f"✅ 成功生成 draw.io 源文件：{drawio_path}")
    print("   内容已与 .md 文档自动同步！")

if __name__ == "__main__":
    generate_drawio()