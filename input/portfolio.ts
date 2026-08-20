export type NavItem = {
  label: string;
  href: string | null;
  disabled?: boolean;
  resume?: boolean;
};

export type ResumeConfig = {
  href: string;
};

export type SocialLink = {
  label: string;
  href: string;
  handle: string;
};

export type Experience = {
  role: string;
  organization: string;
  location: string;
  period: string;
  summary: string;
  highlights: readonly string[];
};

export type CapabilityGroup = {
  title: string;
  description: string;
  items: readonly string[];
};

export type LearningItem = {
  title: string;
  institution: string;
  period: string;
  description: string;
  credentialUrl?: string;
};

export type ProjectVisual = {
  src: string;
  alt: string;
  caption: string;
  width: number;
  height: number;
};

export type WorkflowStep = {
  title: string;
  detail: string;
};

export type CaseStudy = {
  slug: string;
  index: string;
  title: string;
  shortTitle: string;
  eyebrow: string;
  stage: string;
  subtitle?: string;
  summary: string;
  businessProblem: string;
  role: string;
  responsibilities: readonly string[];
  constraints: readonly string[];
  approach: readonly string[];
  decisions: readonly { title: string; detail: string }[];
  implementation: readonly string[];
  validation: readonly string[];
  outcome: string;
  technologies: readonly string[];
  visuals: readonly ProjectVisual[];
  workflow?: readonly WorkflowStep[];
  gallery?: readonly ProjectVisual[];
  featured: boolean;
};

const resumeConfig: ResumeConfig = {
  href: "https://drive.google.com/file/d/1dhrTl5OclFpIHUdxNfGvzWNHyc_V8a4F/view",
};

export const portfolio = {
  site: {
    name: "Ace Relano | AI Engineer, E-commerce & ERP Developer",
    shortName: "Ace Relano",
    // NEEDS_USER_INPUT: Replace with the final Vercel or custom-domain URL after deployment.
    url: "https://ace-relano-portfolio.vercel.app",
    description:
      "Portfolio of Ace Relano, an AI engineer, e-commerce and ERP developer and technical project lead working across configurable products, complex pricing, integrations, cloud infrastructure, and AI-assisted engineering.",
    locale: "en_PH",
  },
  profile: {
    name: "Ace Heart Relano",
    displayName: "Ace Relano",
    initials: "AR",
    role: "AI Engineer / E-commerce & ERP Developer / Technical Project Lead",
    headline:
      "I build and lead e-commerce systems involving complex pricing, configurable products, ERP integrations, and cloud infrastructure.",
    introduction:
      "I work where storefront behavior, business rules, and operational systems meet, turning ambiguous requirements into practical, testable implementation plans.",
    story:
      "My background spans software development, e-commerce delivery, visual design, and customer-facing problem solving. That mix helps me investigate technical detail without losing sight of the people and business processes the system needs to support.",
    location: "Pampanga, Philippines",
    email: "relano.aceheart@gmail.com",
    availability: null,
    resume: resumeConfig,
  },
  navigation: [
    { label: "Work", href: "/work" },
    { label: "About", href: "/about" },
    { label: "Resume", href: null, resume: true },
    { label: "Contact", href: "/contact" },
  ] satisfies readonly NavItem[],
  socials: [
    {
      label: "LinkedIn",
      href: "https://www.linkedin.com/in/ace-heart-relano-a52311139/",
      handle: "ace-heart-relano",
    },
    {
      label: "GitHub",
      href: "https://github.com/ahrelano",
      handle: "@ahrelano",
    },
  ] satisfies readonly SocialLink[],
  experience: [
    {
      role: "Web Developer",
      organization: "Racetronix",
      location: "Remote · Ontario, Canada",
      period: "Jan 2021 - Present",
      summary:
        "Builds and maintains the company’s e-commerce experience while coordinating content, layout, testing, and day-to-day technical problem solving.",
      highlights: [
        "Rebuilt the company website on BigCommerce.",
        "Writes HTML, CSS, and JavaScript to design and update web pages.",
        "Tests across devices and browsers, investigates bugs, and coordinates updates with other teams.",
        "Coordinate technical investigations and testing for e-commerce and ERP initiatives, communicating risks, options, and findings to stakeholders.",
      ],
    },
    {
      role: "Graphic Artist",
      organization: "CV Services Group (Shore 360)",
      location: "Pampanga, Philippines",
      period: "Jun 2020 - Jan 2021",
      summary:
        "Produced accurate sign visualizations and managed production-ready design assets.",
      highlights: [
        "Edited sign photography, corrected colors, and prepared realistic client mockups.",
        "Selected typography, checked production accuracy, and organized digital files.",
      ],
    },
    {
      role: "Graphic Artist",
      organization: "Office Beacon Philippines Inc",
      location: "Pampanga, Philippines",
      period: "Apr 2018 - Jun 2020",
      summary:
        "Created vector graphics and product mockups with an emphasis on visual consistency and organized delivery.",
      highlights: [
        "Converted photos and drawings into high-quality vector graphics.",
        "Prepared presentation mockups and maintained digital design assets.",
      ],
    },
    {
      role: "Customer Service Representative",
      organization: "Sutherland",
      location: "Pampanga, Philippines",
      period: "Oct 2017 - Apr 2018",
      summary:
        "Supported Microsoft customers across phone and chat, combining troubleshooting with accurate transaction handling.",
      highlights: [
        "Troubleshot software and hardware issues for Microsoft products.",
        "Handled order processing, tracking, and transaction records.",
      ],
    },
    {
      role: "Associate Software Engineer Trainee",
      organization: "Cloudstaff",
      location: "Pampanga, Philippines",
      period: "Nov 2016 - Mar 2017",
      summary:
        "Contributed code, testing, and cross-team coordination for an HR web application in an Agile workflow.",
      highlights: [
        "Fixed bugs and added features to an HR website.",
        "Worked with QA and project teams on testing, deployment readiness, and software design.",
      ],
    },
  ] satisfies readonly Experience[],
  capabilities: [
    {
      title: "E-commerce",
      description:
        "Storefront behavior that stays aligned with operational rules.",
      items: [
        "BigCommerce",
        "Stencil customization",
        "Configurable products",
        "Cart behavior",
        "Pricing hierarchies",
        "Quantity discounts",
      ],
    },
    {
      title: "ERP systems",
      description:
        "Practical implementation work across commerce and back-office workflows.",
      items: [
        "Odoo 18 Community",
        "Custom modules",
        "Acumatica 2022 R2",
        "Sales orders",
        "Inventory validation",
        "Migration evaluation",
      ],
    },
    {
      title: "Development",
      description:
        "Readable implementation across the browser, server, and system boundary.",
      items: [
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "Python",
        "HTML & CSS",
      ],
    },
    {
      title: "Design & visual production",
      description:
        "Documented visual-production work from Ace’s public Graphic Artist experience.",
      items: [
        "Photo editing",
        "Graphic design",
        "Sign photography editing",
        "Realistic mockups",
        "Vector graphics",
        "Product mockups",
      ],
    },
    {
      title: "Integrations & APIs",
      description:
        "Integration research, API evaluation, and technical analysis for systems that need a reliable shared contract.",
      items: [
        "REST APIs",
        "Webhook architecture evaluation",
        "JSON",
        "Pricing synchronization evaluation",
        "Customer classes",
        "Technical evaluation",
      ],
    },
    {
      title: "Cloud & infrastructure",
      description:
        "Repeatable environments for implementation, staging, and handoff.",
      items: ["Azure", "Docker", "IIS", "SQL Server", "GitHub", "Vercel"],
    },
    {
      title: "Testing & delivery",
      description:
        "Clear acceptance paths, risk communication, and coordinated execution.",
      items: [
        "Automated testing",
        "Cross-browser QA",
        "Requirements analysis",
        "Technical leadership",
        "Stakeholder communication",
        "Delivery planning",
      ],
    },
    {
      title: "AI engineering foundations",
      description:
        "Applied learning in LLM-assisted development, retrieval-augmented generation, and responsible human-reviewed workflows.",
      items: [
        "Python",
        "Prompt engineering",
        "RAG fundamentals",
        "LangChain",
        "Chroma",
        "Human-in-the-loop review",
      ],
    },
  ] satisfies readonly CapabilityGroup[],
  learning: [
    {
      title: "Bachelor of Science in Information Technology",
      institution: "Don Honorio Ventura State University",
      period: "2013 - 2017",
      description:
        "Foundation in software development, information systems, and technology practice.",
    },
    {
      title: "AI Engineer Core Track: LLM Engineering, RAG, QLoRA, Agents",
      institution: "Udemy",
      period: "Completed July 2026",
      description:
        "Completed coursework covering LLM applications, retrieval-augmented generation, Hugging Face, LangChain, QLoRA fine-tuning, AI agents, and deployment-oriented AI projects.",
      credentialUrl:
        "https://www.udemy.com/certificate/UC-5af0eb1b-4804-4dc8-b780-401815d18cf4/",
    },
    {
      title: "The Data Analyst Course: Complete Data Analyst Bootcamp",
      institution: "Udemy",
      period: "Completed June 2026",
      description:
        "Completed coursework covering Python, NumPy, pandas, data collection, data cleaning, preprocessing, and data visualization.",
      credentialUrl:
        "https://www.udemy.com/certificate/UC-f7a080c8-377c-4839-a318-28dfe9b5ead0/",
    },
    {
      title: "The Complete ASP.NET MVC 5 Course",
      institution: "Udemy",
      period: "Completed December 2020",
      description:
        "Completed coursework covering ASP.NET MVC 5, C#, CRUD workflows, RESTful Web API, Entity Framework, validation, authentication, authorization, and web application deployment.",
      credentialUrl:
        "https://www.udemy.com/certificate/UC-e0159d3c-aabf-417c-8607-03f04a851047/",
    },
  ] satisfies readonly LearningItem[],
  projects: [
    {
      slug: "odoo-18-ecommerce-erp-implementation",
      index: "01",
      title: "Odoo 18 Commerce Platform",
      shortTitle: "Odoo 18 commerce platform",
      eyebrow: "Independent Odoo implementation",
      stage: "Independent project · portfolio-safe demo",
      subtitle:
        "Configured kits, customer pricing, product aliases, and end-to-end order flow",
      summary:
        "An independent Odoo 18 Community implementation demonstrating server-side price resolution, configurable kits, product aliases, and a consistent order flow using synthetic data only.",
      businessProblem:
        "Configure complex kits, customer pricing, aliases, and quantity discounts without losing pricing accuracy or order-line identity across the sales workflow.",
      role: "Independent developer responsible for modeling the commerce rules, building the Odoo 18 Community implementation, and validating the handoff from shopper configuration to ERP documents.",
      responsibilities: [
        "Model pricing, product aliases, configured kits, inventory consumption, and order-line identity.",
        "Build and validate the website-to-ERP workflow with privacy-safe synthetic data.",
        "Keep customer-facing configuration constrained to validated options and server-resolved prices.",
      ],
      constraints: [
        "Pricing must stay authoritative when customer-specific rules, quantity discounts, kits, and add-ons interact.",
        "Aliases need their own sellable SKUs and units of measure while consuming shared base inventory correctly.",
        "The portal must reveal only intended kit data while rejecting invalid option access and client-supplied prices.",
      ],
      approach: [
        "Model the storefront, cart, quotation, sales order, delivery, and invoice as one connected workflow.",
        "Resolve prices and validate configuration on the server instead of trusting browser state.",
        "Use representative synthetic scenarios to test rule precedence, shared inventory, and document continuity.",
      ],
      decisions: [
        {
          title: "Server-side pricing authority",
          detail:
            "The storefront requests a price, but Odoo evaluates the pricing hierarchy. Customer-specific rules and quantity discounts remain authoritative beyond the browser session.",
        },
        {
          title: "Aliases share real inventory",
          detail:
            "An alias can carry a separate SKU and selling unit while its fulfillment demand is translated back to the shared base item, preventing a second inventory truth.",
        },
        {
          title: "Portal-safe kit projection",
          detail:
            "A portal-access regression was resolved with a narrowly scoped, validated projection of only the kit data intentionally exposed to shoppers.",
        },
      ],
      implementation: [
        "A server-side pricing hierarchy with customer-specific pricing and quantity discounts.",
        "Product aliases with separate SKUs and selling units of measure that consume shared base inventory.",
        "Fixed-price and component-sum configurable kits with required selections, substitutions, optional components, None selections, and priced add-ons.",
        "Configured-kit identity preserved from the website cart through quotation, sales order, delivery, and invoice.",
        "Validated option access and server-side price resolution for a portal-safe configuration experience.",
      ],
      workflow: [
        {
          title: "Configure in the storefront",
          detail:
            "A shopper selects a fixed-price or component-sum kit, including required choices, substitutions, optional components, None selections, and priced add-ons.",
        },
        {
          title: "Resolve price and retain identity",
          detail:
            "Odoo validates the selected options and resolves the applicable price on the server before the configured kit moves into the cart and quotation flow.",
        },
        {
          title: "Carry the kit into fulfillment",
          detail:
            "The configured identity is retained through the sales order, delivery, and invoice while aliases consume the correct shared base inventory.",
        },
      ],
      validation: [
        "Fixed-price and component-sum kit scenarios resolve to $375 USD and $280 USD respectively in the synthetic demo.",
        "Field Kit ×2 resolves to $712.50 after a 5% discount; Signal Cable Pack ×3 resolves to $256.50 after 5% while consuming 18 base units.",
        "A complete synthetic demo order carries a $1,249 USD total from cart through the final documents.",
        "Regression checks cover portal access, server-side option validation, price resolution, and configured-kit continuity.",
      ],
      outcome:
        "A portfolio-safe Odoo 18 Commerce implementation that keeps price resolution server-side and carries each configured kit from the storefront through delivery and invoicing. All products, customers, prices, images, and order documents shown are synthetic.",
      technologies: [
        "Odoo 18 Community",
        "Python",
        "PostgreSQL 15",
        "Docker",
        "Git/GitHub",
      ],
      visuals: [
        {
          src: "/images/projects/odoo18-commerce-platform/02-fixed-kit-configurator-desktop.webp",
          alt: "Synthetic Odoo storefront showing a fixed-price configurable kit with validated component options.",
          caption:
            "Fixed-price kit configuration in the independent Odoo 18 Community demo. All product and price data is synthetic.",
          width: 1600,
          height: 1000,
        },
      ],
      gallery: [
        {
          src: "/images/projects/odoo18-commerce-platform/01-storefront-desktop.webp",
          alt: "Synthetic Odoo storefront displaying the available commerce products and kits.",
          caption:
            "Storefront overview with synthetic products, customers, and pricing.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/02-fixed-kit-configurator-desktop.webp",
          alt: "Synthetic Odoo storefront showing a fixed-price configurable kit with validated component options.",
          caption:
            "Fixed-price kit configuration with required selections and priced add-ons.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/03-component-sum-configurator-desktop.webp",
          alt: "Synthetic Odoo storefront showing a component-sum kit with its calculated configuration price.",
          caption:
            "Component-sum kit configuration, where the selected components determine the price.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/04-alias-pack-pricing-desktop.webp",
          alt: "Synthetic Odoo product page showing alias-pack pricing and quantity-based pricing information.",
          caption:
            "Alias-pack pricing with a distinct selling SKU and unit of measure backed by shared inventory.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/05-cart-desktop.webp",
          alt: "Synthetic Odoo cart showing configured commerce items before checkout.",
          caption:
            "Cart view retaining the configured-kit identity before quotation and order creation.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/06-sales-order-desktop.webp",
          alt: "Synthetic Odoo sales order showing the configured-kit details after the storefront workflow.",
          caption:
            "Sales order showing the configured kit after server-side validation and price resolution.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/07-delivery-kit-overview-desktop.webp",
          alt: "Synthetic Odoo delivery view showing the configured kit and its fulfillment components.",
          caption:
            "Delivery overview showing the fulfillment-side representation of the configured kit.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/08-invoice-desktop.webp",
          alt: "Synthetic Odoo invoice showing a completed commerce order.",
          caption:
            "Invoice view completing the synthetic end-to-end order flow.",
          width: 1600,
          height: 1000,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/09-fixed-kit-configurator-mobile.webp",
          alt: "Mobile synthetic Odoo storefront showing a fixed-price kit configurator.",
          caption:
            "Mobile fixed-price kit configuration, designed to keep component choices legible on a narrow screen.",
          width: 390,
          height: 844,
        },
        {
          src: "/images/projects/odoo18-commerce-platform/10-cart-mobile.webp",
          alt: "Mobile synthetic Odoo cart showing configured commerce items.",
          caption:
            "Mobile cart view retaining the configured-kit context before checkout.",
          width: 390,
          height: 844,
        },
      ],
      featured: true,
    },
    {
      slug: "bigcommerce-acumatica-integration",
      index: "02",
      title: "BigCommerce and Acumatica Integration",
      shortTitle: "BigCommerce and Acumatica",
      eyebrow: "Integration evaluation",
      stage: "Research and technical evaluation",
      summary:
        "A technical evaluation of cart events, customer-class pricing, quantity breaks, and the boundary between storefront responsiveness and ERP authority.",
      businessProblem:
        "The storefront needs timely pricing while the ERP holds customer and quantity-dependent rules. Any integration approach must account for API limits, event timing, failures, and differences between the two systems' pricing models.",
      role: "Technical researcher and project lead evaluating platform APIs, pricing responsibilities, webhook-based approaches, and feasible synchronization patterns.",
      responsibilities: [
        "Research BigCommerce and Acumatica API capabilities and constraints.",
        "Map customer-class and quantity-break requirements across both systems.",
        "Document architectural tradeoffs, failure modes, and evaluation findings.",
      ],
      constraints: [
        "Cart webhooks are event-driven and may not fit every synchronous pricing decision.",
        "Customer-class and quantity-break models differ across platform boundaries.",
        "Retries, partial failures, API limits, and stale data must be considered explicitly.",
      ],
      approach: [
        "Start with an ownership map for customer, product, price, and order data.",
        "Evaluate synchronous lookup, scheduled synchronization, and hybrid patterns.",
        "Use failure scenarios to assess whether each option can degrade safely.",
      ],
      decisions: [
        {
          title: "Establish system authority",
          detail:
            "Define which platform owns each piece of data before choosing webhook or synchronization behavior.",
        },
        {
          title: "Separate event transport from price logic",
          detail:
            "A webhook can signal a change, but the pricing contract still needs deterministic inputs, precedence, and fallback behavior.",
        },
        {
          title: "Design for replay",
          detail:
            "Treat retries and idempotency as core requirements so transient failures do not duplicate or corrupt state.",
        },
      ],
      implementation: [
        "Integration architecture and pricing-synchronization research.",
        "Customer-class and quantity-break requirement mapping.",
        "API capability and constraint analysis.",
        "Failure-mode, retry, and data-ownership evaluation.",
      ],
      validation: [
        "Architecture walkthroughs using representative pricing and cart scenarios.",
        "Event-sequence reviews for updates, retries, and stale-data risks.",
        "Feasibility assessment against the required pricing scenarios.",
      ],
      outcome:
        "This work represents research and technical evaluation. Middleware and webhook implementation were handled separately, and no production deployment or business impact is claimed.",
      technologies: [
        "BigCommerce",
        "Acumatica 2022 R2",
        "REST API evaluation",
        "Webhook architecture evaluation",
        "JSON",
      ],
      visuals: [
        {
          src: "/images/projects/bigcommerce-acumatica-flow.svg",
          alt: "Conceptual integration architecture connecting a BigCommerce cart, an integration layer, pricing rules, and Acumatica ERP.",
          caption:
            "Conceptual integration flow with fictional events and identifiers. It illustrates system boundaries without exposing client infrastructure.",
          width: 1600,
          height: 1000,
        },
      ],
      featured: true,
    },
    {
      slug: "acumatica-azure-staging-environment",
      index: "03",
      title: "Acumatica Azure Staging Environment",
      shortTitle: "Acumatica Azure staging",
      eyebrow: "Cloud infrastructure",
      stage: "Staging environment implementation",
      summary:
        "A staging-environment workflow for Acumatica 2022 R2 covering Azure infrastructure, SQL Server, IIS, snapshot restoration, customization publishing, access, and handoff.",
      businessProblem:
        "ERP customization and upgrade work needs an isolated environment that is representative enough for testing while remaining controlled, repeatable, and safe to hand over to project participants.",
      role: "Developer and technical coordinator responsible for environment setup, restoration and publishing steps, access coordination, testing support, and handoff documentation.",
      responsibilities: [
        "Coordinate the Azure, Windows, SQL Server, IIS, and Acumatica setup sequence.",
        "Restore approved snapshots and publish required customizations.",
        "Support access, validation, and environment handoff.",
      ],
      constraints: [
        "Version alignment matters across Acumatica, the database, and published customizations.",
        "Snapshots and credentials require careful handling and must not enter public documentation.",
        "The environment needs useful parity without exposing production systems or data.",
      ],
      approach: [
        "Build the environment as a documented sequence with clear prerequisites and checkpoints.",
        "Separate infrastructure readiness, application restoration, customization publishing, and user validation.",
        "Use sanitized descriptions in the public portfolio and keep operational values private.",
      ],
      decisions: [
        {
          title: "Stage by dependency",
          detail:
            "Bring up infrastructure, database, web tier, application, and customization layers in an order that makes failures easier to isolate.",
        },
        {
          title: "Protect environment detail",
          detail:
            "Describe the architecture publicly without publishing hostnames, credentials, database names, or access paths.",
        },
        {
          title: "Handoff is part of implementation",
          detail:
            "Include access confirmation, validation steps, and owner-facing documentation in the definition of a usable staging environment.",
        },
      ],
      implementation: [
        "Azure virtual infrastructure for a controlled staging workload.",
        "SQL Server and IIS prerequisites for Acumatica 2022 R2.",
        "Snapshot restoration and customization publishing workflow.",
        "Access coordination, testing support, and environment handoff.",
      ],
      validation: [
        "Infrastructure and service-readiness checks.",
        "Application access and restored-data verification using approved test procedures.",
        "Customization publication and role-based handoff checks.",
      ],
      outcome:
        "A controlled Acumatica 2022 R2 staging environment prepared for isolated testing, customization validation, and approved stakeholder access. This is not presented as a production deployment or performance benchmark.",
      technologies: [
        "Microsoft Azure",
        "Acumatica 2022 R2",
        "Windows Server",
        "SQL Server",
        "IIS",
      ],
      visuals: [
        {
          src: "/images/projects/acumatica-azure-staging.svg",
          alt: "Conceptual Azure staging architecture with access control, IIS and Acumatica, SQL Server, snapshot restore, and testing handoff.",
          caption:
            "Conceptual staging architecture. All labels are generic and no real hostnames, credentials, database values, or client data are shown.",
          width: 1600,
          height: 1000,
        },
      ],
      featured: false,
    },
  ] satisfies readonly CaseStudy[],
  seo: {
    keywords: [
      "Ace Relano",
      "e-commerce developer",
      "ERP developer",
      "technical project lead",
      "BigCommerce developer",
      "Odoo developer",
      "Acumatica integration",
    ],
  },
} as const;

export const featuredProjects = portfolio.projects.filter(
  (project) => project.featured,
);

export function getProject(slug: string) {
  return portfolio.projects.find((project) => project.slug === slug);
}

export function absoluteUrl(path = "") {
  return new URL(path, portfolio.site.url).toString();
}
