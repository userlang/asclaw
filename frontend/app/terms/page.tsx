// 作者：langjunnan
// 开发时间：2025年7月23日

import LayoutApp from "@/components/layout/layout-app"
import { APP_DOMAIN, APP_NAME } from "@/lib/config"
import type { Metadata } from "next"

export const metadata: Metadata = {
  title: `服务条款 - ${APP_NAME}`,
  description: `${APP_NAME} 服务条款 - 使用我们服务前请仔细阅读以下条款。`,
}

export default function TermsPage() {
  const lastUpdated = "2026年11月6日"

  return (
    <LayoutApp>
      <div className="mx-auto max-w-4xl px-4 pt-24 pb-16 sm:px-6 lg:px-8">
        <div className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight text-foreground">
            服务条款
          </h1>
          <p className="mt-3 text-muted-foreground">最后更新：{lastUpdated}</p>
        </div>

        <div className="prose prose-neutral dark:prose-invert max-w-none space-y-10 text-foreground">
          <section>
            <p className="text-muted-foreground leading-relaxed">
              欢迎使用 {APP_NAME}（以下简称"本平台"）。本服务条款（以下简称"条款"）是您与{" "}
              {APP_NAME} 之间关于使用{" "}
              <span className="font-medium">{APP_DOMAIN}</span>{" "}
              及相关服务所达成的协议。请在使用我们的服务之前仔细阅读本条款。访问或使用我们的服务，即表示您同意受这些条款的约束。
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              1. 服务说明
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              {APP_NAME} 是一个 AI Agent 构建平台，提供 MCP（Model Context Protocol）工具集成、Skill 编排和智能对话等服务。我们允许企业用户通过一行代码接入开放的 MCP 工具生态，构建能够理解和执行复杂任务的 AI Agent。我们保留随时修改、暂停或终止部分或全部服务的权利，并将尽合理努力提前通知用户。
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              2. 企业入驻与账号
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  2.1 企业入驻申请
                </h3>
                <p>
                  本平台面向企业提供服务，不向个人开放注册。企业入驻须通过入驻申请页面提交企业资质信息（包括企业名称、统一社会信用代码、法定代表人、联系人姓名、联系电话、联系邮箱、注册地址及企业简介等），并设置企业登录账号（用户名和密码）。申请提交后由平台管理员审核，审核通过后方可使用该企业账号登录平台。您须确保所提交的信息真实、准确、完整，并在信息发生变更时及时更新。
                </p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  2.2 账号安全
                </h3>
                <p>
                  您负责妥善保管企业账号的用户名和密码，并对使用该账号进行的所有活动负责。请勿将账号凭据披露或转让给任何未经授权的第三方。如发现任何未经授权的使用，请立即联系我们。我们不对因您未能妥善保管账号凭据而导致的损失承担责任。
                </p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  2.3 入驻资格
                </h3>
                <p>
                  申请入驻的主体须为依据适用法律合法设立并有效存续的企业或其他组织。提交入驻申请即表示您声明并保证：您已获得该企业的合法授权，所提交的资质信息真实有效，且联系人为具有完全民事行为能力并经企业授权的自然人。平台有权自主决定是否通过入驻审核，并有权拒绝或终止为提交虚假资质信息的主体提供服务。
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              3. 使用规范
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  3.1 禁止行为
                </h3>
                <p className="mb-2">您同意不从事以下行为：</p>
                <ul className="list-disc list-inside space-y-1.5 pl-2">
                  <li>违反任何适用的法律法规</li>
                  <li>侵犯他人的知识产权、隐私权或其他权利</li>
                  <li>传播恶意软件、病毒或其他有害代码</li>
                  <li>试图未经授权访问我们的系统或其他用户的账户</li>
                  <li>使用本平台进行欺诈、诈骗或其他违法活动</li>
                  <li>通过自动化手段过度访问或滥用平台资源</li>
                  <li>干扰或破坏平台的正常运行</li>
                  <li>生成或传播违法、有害、歧视性或侵权内容</li>
                  <li>冒充他人或虚假陈述您与他人的关系</li>
                </ul>
              </div>
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  3.2 AI 使用规范
                </h3>
                <p>
                  使用 AI 功能时，您不得将其用于生成虚假信息、操纵内容、实施欺骗行为或任何有害目的。您对通过本平台生成的内容及其使用方式负有责任。
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              4. 知识产权
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  4.1 平台权利
                </h3>
                <p>
                  {APP_NAME} 平台及其原始内容、功能和技术均为我们或我们的许可方所有，受知识产权法保护。未经明确书面授权，您不得复制、分发、修改或创作基于平台的衍生作品。
                </p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  4.2 用户内容
                </h3>
                <p>
                  您保留对您在平台上创建的内容（如 Agent 配置、自定义 Skill 等）的所有权。通过上传或提交内容，您授予我们一个非独占的、全球性的许可，以运营、改进和推广我们的服务。
                </p>
              </div>
              <div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                  4.3 第三方软件组件
                </h3>
                <p>本平台使用了第三方软件组件。相关许可信息可在相应组件的官方文档中查阅。</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              5. 使用限制与配额
            </h2>
            <div className="space-y-2 text-muted-foreground leading-relaxed">
              <p>
                为确保平台的稳定运行，我们对平台使用设有一定限制：
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li>平台功能的使用配额以经审核入驻的企业账号为单位进行管理</li>
                <li>文件上传数量及大小有相应限制</li>
                <li>API 调用频率受速率限制约束</li>
              </ul>
              <p>
                我们可能根据服务运营情况调整上述限制，并将提前通知企业用户。
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              6. 第三方服务
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              我们的平台可能包含第三方 MCP 工具、AI 模型及其他第三方服务的链接或集成。这些第三方服务由各自的服务提供商运营，适用其各自的服务条款和隐私政策。我们不对第三方服务的内容、可用性或安全性承担责任。使用第三方服务前，请查阅相关服务商的条款。
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              7. 免责声明
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                本平台及其服务按"现状"提供，不附带任何明示或暗示的保证。我们不保证服务不中断、无错误或满足您的特定需求。
              </p>
              <p>
                AI 生成的内容仅供参考，可能存在错误或不准确之处。您应对使用 AI 输出结果自行判断，并承担相应责任。我们不对依赖 AI 生成内容而产生的任何损失承担责任。
              </p>
              <p>
                在适用法律允许的最大范围内，我们对因使用或无法使用本服务而产生的任何间接、附带、特殊、后果性或惩罚性损害不承担责任。
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              8. 赔偿
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              您同意就您违反本条款、滥用服务或侵犯他人权利而引起的任何索赔、损害、损失、费用（包括合理的律师费）对 {APP_NAME} 及其关联方进行赔偿并使其免受损害。
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              9. 账号终止
            </h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                您可以联系平台管理员申请注销企业账号。我们保留在以下情况下暂停或终止企业账号的权利：
              </p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li>提供虚假、失效的企业资质信息</li>
                <li>违反本服务条款</li>
                <li>从事欺诈或非法活动</li>
                <li>其他我们认为必要的情况</li>
              </ul>
              <p>
                账号终止后，您在平台上的数据可能被删除。我们建议您定期导出重要数据。
              </p>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              10. 条款变更
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              我们可能随时修改本服务条款。对于重大变更，我们将通过平台通知或电子邮件提前告知您。变更生效后继续使用本服务，即视为您接受修订后的条款。建议您定期查阅本页面以了解最新条款。
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold text-foreground mb-4">
              11. 适用法律
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              本条款受中华人民共和国法律管辖并依其解释。与本条款相关的任何争议，双方应首先协商解决；协商不成的，提交有管辖权的人民法院裁决。
            </p>
          </section>
        </div>
      </div>
    </LayoutApp>
  )
}
