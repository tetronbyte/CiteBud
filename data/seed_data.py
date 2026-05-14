"""
CiteBud — Milestone 2 Seed Data Generator
==========================================
Generates realistic academic data for all 11 tables and outputs seed.sql.

Usage:
    pip install -r requirements.txt
    python data/seed_data.py

Output:
    data/seed.sql  — INSERT statements ready to load after schema.sql
"""

import hashlib
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from faker import Faker
from sentence_transformers import SentenceTransformer

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ─── Configuration ───────────────────────────────────────────────────────────

NUM_STUDENTS = 20
NUM_DOCUMENTS = 50
NUM_TOPICS = 30
NUM_QUERIES = 150
NUM_SOLUTIONS = 100
TARGET_CHUNKS = 800

OUTPUT_PATH = Path(__file__).parent / "seed.sql"

# ─── Academic content pools ──────────────────────────────────────────────────

COURSES = [
    ("CS3010", "Data Structures and Algorithms"),
    ("CS3020", "Database Management Systems"),
    ("CS3030", "Operating Systems"),
    ("CS3040", "Computer Networks"),
    ("CS3050", "Machine Learning"),
    ("CS4010", "Distributed Systems"),
    ("MA2010", "Linear Algebra"),
    ("MA2020", "Probability and Statistics"),
    ("PH2010", "Classical Mechanics"),
    ("PH2020", "Electromagnetism"),
]

TOPIC_NAMES = [
    "Binary Search Trees", "Hash Tables", "Graph Algorithms", "Dynamic Programming",
    "Sorting Algorithms", "SQL Joins", "Database Normalization", "Transaction Isolation",
    "Query Optimization", "Indexing Strategies", "Process Scheduling", "Memory Management",
    "Virtual Memory", "TCP/IP Protocol", "Network Security", "Neural Networks",
    "Gradient Descent", "Linear Regression", "Eigenvalues", "Matrix Decomposition",
    "Vector Spaces", "Bayesian Inference", "Hypothesis Testing", "Confidence Intervals",
    "Newton's Laws", "Conservation of Energy", "Rotational Dynamics",
    "Maxwell's Equations", "Electromagnetic Waves", "Gauss's Law",
]

# Realistic chunk content templates (filled per topic for variety)
CHUNK_TEMPLATES = {
    "Binary Search Trees": [
        "A binary search tree (BST) is a rooted binary tree where each node stores a key greater than all keys in its left subtree and less than those in its right subtree. This ordering property enables O(log n) average-case search, insertion, and deletion operations.",
        "The worst-case time complexity of BST operations degrades to O(n) when the tree becomes skewed. Self-balancing variants like AVL trees and Red-Black trees maintain O(log n) guarantees by enforcing height constraints after each modification.",
        "In-order traversal of a BST yields keys in sorted order. This property makes BSTs useful for implementing ordered dictionaries and priority queues where range queries are needed.",
        "Deletion in a BST has three cases: deleting a leaf node (trivial removal), deleting a node with one child (replace with child), and deleting a node with two children (replace with in-order successor or predecessor).",
    ],
    "Hash Tables": [
        "A hash table maps keys to values using a hash function that computes an index into an array of buckets. The average-case time complexity for lookup, insert, and delete is O(1), making hash tables essential for constant-time dictionary operations.",
        "Collision resolution strategies include chaining (each bucket stores a linked list of entries) and open addressing (probing for the next empty slot). The choice affects cache performance and worst-case behavior.",
        "The load factor alpha = n/m (items/buckets) determines performance. When alpha exceeds a threshold (typically 0.75), the table is resized and all entries rehashed to maintain expected constant-time operations.",
        "Universal hashing selects a hash function randomly from a family of functions, providing probabilistic guarantees against adversarial inputs. This prevents the O(n) worst case that a fixed hash function might encounter.",
    ],
    "Graph Algorithms": [
        "Breadth-first search (BFS) explores vertices level by level using a queue, guaranteeing shortest paths in unweighted graphs. Its time complexity is O(V + E) where V is vertices and E is edges.",
        "Dijkstra's algorithm finds shortest paths from a source vertex to all other vertices in graphs with non-negative edge weights. Using a min-heap, it achieves O((V + E) log V) time complexity.",
        "A minimum spanning tree connects all vertices with minimum total edge weight. Kruskal's algorithm sorts edges and greedily adds them using a union-find structure in O(E log E) time.",
        "Topological sorting produces a linear ordering of vertices in a directed acyclic graph (DAG) such that for every edge (u, v), u appears before v. It is used for task scheduling and dependency resolution.",
    ],
    "Dynamic Programming": [
        "Dynamic programming solves optimization problems by breaking them into overlapping subproblems and storing intermediate results. The key insight is optimal substructure: an optimal solution contains optimal solutions to its subproblems.",
        "The two implementation approaches are top-down (memoization with recursion) and bottom-up (tabulation with iteration). Bottom-up avoids recursion overhead but requires understanding the dependency order of subproblems.",
        "The longest common subsequence (LCS) problem has a classic DP solution using a 2D table where entry (i,j) stores the LCS length of the first i characters of string X and first j characters of string Y.",
        "The knapsack problem demonstrates DP's power: given items with weights and values and a weight capacity W, determine the maximum value achievable. The 0/1 variant uses O(nW) time and space.",
    ],
    "Sorting Algorithms": [
        "Merge sort is a divide-and-conquer algorithm that recursively splits an array in half, sorts each half, and merges the sorted halves. It guarantees O(n log n) time in all cases but requires O(n) auxiliary space.",
        "Quicksort partitions the array around a pivot element and recursively sorts the partitions. Its average case is O(n log n) with O(log n) space, but worst case degrades to O(n^2) with poor pivot selection.",
        "Counting sort is a non-comparison-based algorithm that counts occurrences of each value, achieving O(n + k) time where k is the range of input values. It is stable and efficient when k is not significantly larger than n.",
        "The lower bound for comparison-based sorting is Omega(n log n), proven by the decision tree model. This means no comparison sort can do better than n log n comparisons in the worst case.",
    ],
    "SQL Joins": [
        "An inner join returns only rows where the join condition is satisfied in both tables. It is the most common join type and produces the intersection of matching rows based on the specified columns.",
        "A left outer join returns all rows from the left table and matching rows from the right table. Where no match exists, NULL values fill the right table's columns, preserving all left-side records.",
        "A cross join produces the Cartesian product of two tables — every row from the first table paired with every row from the second. It is rarely used intentionally but useful for generating combinations.",
        "Self-joins join a table to itself using aliases, useful for hierarchical data like employee-manager relationships or finding pairs within the same table that satisfy a condition.",
    ],
    "Database Normalization": [
        "First normal form (1NF) requires that all column values are atomic (indivisible) and that each row is uniquely identifiable. Repeating groups and multi-valued attributes must be decomposed into separate rows or tables.",
        "Second normal form (2NF) eliminates partial dependencies: every non-prime attribute must depend on the entire candidate key, not just part of it. This is relevant only for tables with composite primary keys.",
        "Third normal form (3NF) removes transitive dependencies: no non-prime attribute should depend on another non-prime attribute. If A → B → C, then C should be moved to a separate table keyed by B.",
        "Boyce-Codd normal form (BCNF) strengthens 3NF by requiring that for every functional dependency X → Y, X must be a superkey. The difference from 3NF arises when a prime attribute depends on a non-superkey.",
    ],
    "Transaction Isolation": [
        "The ACID properties — Atomicity, Consistency, Isolation, Durability — define reliable transaction processing. Isolation ensures that concurrent transactions do not interfere with each other's intermediate states.",
        "Read Committed isolation prevents dirty reads but allows non-repeatable reads: a transaction may see different values if it reads the same row twice while another transaction commits between the reads.",
        "Serializable isolation is the strongest level, ensuring that concurrent transaction execution produces results equivalent to some serial ordering. It prevents all anomalies but may reduce throughput due to locking or aborts.",
        "Phantom reads occur when a transaction re-executes a range query and finds new rows inserted by another committed transaction. Repeatable Read prevents this in some implementations using gap locks.",
    ],
    "Query Optimization": [
        "The query optimizer transforms a declarative SQL statement into an efficient execution plan by exploring equivalent algebraic expressions and choosing the one with lowest estimated cost based on table statistics.",
        "Cost-based optimization uses statistics like table cardinality, column selectivity, and index availability to estimate the I/O and CPU cost of candidate plans. Outdated statistics can lead to suboptimal plan choices.",
        "Predicate pushdown moves filter conditions as close to the data source as possible, reducing the number of rows processed by upstream operators. This is one of the most impactful logical optimizations.",
        "Join ordering is critical: for N tables, there are N! possible orderings. The optimizer uses heuristics and dynamic programming to find a near-optimal order that minimizes intermediate result sizes.",
    ],
    "Indexing Strategies": [
        "A B-tree index maintains sorted data in a balanced tree structure, supporting equality and range lookups in O(log n) time. It is the default index type in most relational databases.",
        "A composite index on columns (A, B, C) supports queries filtering on A, or (A, B), or (A, B, C) — the leftmost prefix rule. It cannot efficiently serve queries that filter only on B or C without A.",
        "Covering indexes include all columns needed by a query, enabling index-only scans that avoid heap lookups entirely. This trades storage space for significant read performance improvement.",
        "Hash indexes provide O(1) equality lookups but do not support range queries or ordering. They are useful for exact-match workloads like cache key lookups and equality joins.",
    ],
    "Process Scheduling": [
        "Round-robin scheduling assigns each process a fixed time quantum and cycles through the ready queue. It provides fair CPU sharing and bounded response time but may cause excessive context switching with small quanta.",
        "Priority scheduling assigns CPU to the highest-priority process. Starvation of low-priority processes is addressed through aging: gradually increasing the priority of waiting processes over time.",
        "The Completely Fair Scheduler (CFS) in Linux uses a red-black tree keyed by virtual runtime to ensure each process receives a proportional share of CPU time, approximating ideal fair scheduling.",
        "Multilevel feedback queues use multiple priority levels with different scheduling policies. Processes move between queues based on behavior: CPU-bound processes sink to lower priorities while I/O-bound processes rise.",
    ],
    "Memory Management": [
        "Paging divides physical memory into fixed-size frames and logical memory into same-sized pages. A page table maps virtual page numbers to physical frame numbers, eliminating external fragmentation.",
        "The translation lookaside buffer (TLB) is a hardware cache of recent page table entries. TLB hits avoid the costly memory access for page table lookup, making virtual memory practical with acceptable overhead.",
        "Memory allocation algorithms include first-fit (allocate first sufficient block), best-fit (smallest sufficient block), and worst-fit (largest block). First-fit generally provides the best combination of speed and utilization.",
        "Segmentation divides memory into variable-sized segments reflecting logical program structure (code, data, stack). Unlike paging, it preserves the programmer's view of memory but suffers from external fragmentation.",
    ],
    "Virtual Memory": [
        "Virtual memory allows processes to use more memory than physically available by storing inactive pages on disk. The operating system manages page-in and page-out operations transparently.",
        "Page replacement algorithms determine which page to evict when a page fault occurs and no free frames exist. LRU (Least Recently Used) evicts the page unused for the longest time, approximating optimal replacement.",
        "Thrashing occurs when a system spends more time paging than executing useful work, typically because the working set of active processes exceeds available physical memory. The solution is to reduce multiprogramming degree.",
        "Demand paging loads pages only when accessed (on first page fault), avoiding the cost of loading entire programs into memory at startup. This reduces initial load time and memory consumption.",
    ],
    "TCP/IP Protocol": [
        "TCP provides reliable, ordered, byte-stream delivery over IP using sequence numbers, acknowledgments, and retransmission. The three-way handshake (SYN, SYN-ACK, ACK) establishes a connection before data transfer.",
        "TCP flow control uses a sliding window mechanism where the receiver advertises its available buffer space. The sender limits unacknowledged data to the window size, preventing receiver buffer overflow.",
        "TCP congestion control algorithms (slow start, congestion avoidance, fast retransmit, fast recovery) dynamically adjust the sending rate to avoid network congestion while maximizing throughput.",
        "The IP layer provides best-effort, connectionless packet delivery with source and destination addressing. IPv4 uses 32-bit addresses while IPv6 extends to 128-bit addresses to accommodate the growing internet.",
    ],
    "Network Security": [
        "TLS (Transport Layer Security) provides encrypted communication between client and server through a handshake that negotiates cipher suites, authenticates the server via certificates, and establishes session keys.",
        "Public-key cryptography uses asymmetric key pairs: a public key for encryption and a private key for decryption. RSA and elliptic-curve algorithms enable secure key exchange without pre-shared secrets.",
        "Firewalls filter network traffic based on rules examining packet headers (source/destination IP, port, protocol). Stateful firewalls track connection state and can make decisions based on traffic patterns.",
        "SQL injection attacks exploit improperly sanitized user input in database queries. Parameterized queries (prepared statements) prevent injection by separating SQL structure from user-supplied data.",
    ],
    "Neural Networks": [
        "A feedforward neural network consists of layers of neurons where information flows from input through hidden layers to output. Each neuron computes a weighted sum of inputs, applies a nonlinear activation function, and passes the result forward.",
        "Backpropagation computes gradients of the loss function with respect to each weight by applying the chain rule layer by layer from output to input. These gradients drive the weight updates during training.",
        "Activation functions introduce nonlinearity: sigmoid maps to (0,1), tanh to (-1,1), and ReLU(x) = max(0,x). ReLU is preferred in deep networks because it mitigates the vanishing gradient problem.",
        "Overfitting occurs when a network memorizes training data rather than learning generalizable patterns. Regularization techniques include dropout (randomly zeroing neurons during training), L2 weight decay, and early stopping.",
    ],
    "Gradient Descent": [
        "Gradient descent minimizes a loss function by iteratively updating parameters in the direction of steepest descent: theta = theta - alpha * gradient(L). The learning rate alpha controls step size.",
        "Stochastic gradient descent (SGD) computes gradients on random mini-batches rather than the full dataset, trading accuracy for speed. This introduces noise that can help escape local minima.",
        "Adam optimizer combines momentum (exponential moving average of gradients) with RMSprop (adaptive learning rates per parameter), providing robust convergence across a wide range of problems.",
        "The learning rate schedule reduces alpha over training time. Common strategies include step decay, cosine annealing, and warmup followed by decay. Too high a rate causes divergence; too low causes slow convergence.",
    ],
    "Linear Regression": [
        "Linear regression models the relationship between a dependent variable y and independent variables X as y = X*beta + epsilon, where beta is estimated by minimizing the sum of squared residuals.",
        "The ordinary least squares (OLS) estimator beta_hat = (X^T X)^{-1} X^T y is the best linear unbiased estimator (BLUE) under the Gauss-Markov assumptions: linearity, exogeneity, homoscedasticity, and no multicollinearity.",
        "R-squared measures the proportion of variance in y explained by the model. Adjusted R-squared penalizes for additional predictors, addressing the problem that R-squared never decreases when adding variables.",
        "Multicollinearity occurs when predictor variables are highly correlated, inflating variance of coefficient estimates. Variance Inflation Factor (VIF) quantifies this: VIF > 10 suggests problematic collinearity.",
    ],
    "Eigenvalues": [
        "An eigenvalue lambda of matrix A satisfies Av = lambda*v for some nonzero vector v (the eigenvector). The eigenvalues are found by solving the characteristic equation det(A - lambda*I) = 0.",
        "The spectral theorem states that every real symmetric matrix is orthogonally diagonalizable: A = Q*Lambda*Q^T where Q contains orthonormal eigenvectors and Lambda is diagonal with eigenvalues.",
        "Principal Component Analysis (PCA) uses eigendecomposition of the covariance matrix to find orthogonal directions of maximum variance in data, enabling dimensionality reduction while preserving information.",
        "The power iteration method computes the dominant eigenvalue by repeatedly multiplying a vector by A and normalizing. It converges at a rate proportional to |lambda_1/lambda_2|, the ratio of the two largest eigenvalues.",
    ],
    "Matrix Decomposition": [
        "LU decomposition factors a matrix A into a lower triangular matrix L and an upper triangular matrix U, enabling efficient solution of linear systems Ax = b by forward and back substitution.",
        "Singular Value Decomposition (SVD) factorizes any m x n matrix as A = U*Sigma*V^T where U and V are orthogonal and Sigma is diagonal with singular values. It reveals rank, null space, and optimal low-rank approximations.",
        "QR decomposition expresses A as the product of an orthogonal matrix Q and upper triangular R. It is numerically stable and forms the basis of the QR algorithm for computing eigenvalues.",
        "The Cholesky decomposition A = L*L^T applies to symmetric positive-definite matrices and is twice as efficient as LU decomposition. It is widely used in statistics for sampling multivariate normal distributions.",
    ],
    "Vector Spaces": [
        "A vector space over a field F is a set V with addition and scalar multiplication satisfying closure, associativity, commutativity, identity, and inverse axioms. Common examples include R^n and function spaces.",
        "Linear independence means no vector in a set can be written as a linear combination of the others. The maximum number of linearly independent vectors in V is its dimension, dim(V).",
        "A basis for V is a linearly independent spanning set. Every vector in V has a unique representation as a linear combination of basis vectors. Different bases give different coordinate representations.",
        "A linear transformation T: V → W preserves addition and scalar multiplication. Its kernel (null space) and image (range) are subspaces, connected by the rank-nullity theorem: dim(ker T) + dim(im T) = dim(V).",
    ],
    "Bayesian Inference": [
        "Bayes' theorem updates prior beliefs given evidence: P(theta|data) = P(data|theta) * P(theta) / P(data). The posterior combines the likelihood of observed data with prior knowledge about parameters.",
        "Conjugate priors simplify Bayesian computation: when the prior and likelihood belong to a conjugate family, the posterior has the same distributional form as the prior with updated parameters.",
        "Markov Chain Monte Carlo (MCMC) methods sample from complex posterior distributions by constructing a Markov chain whose stationary distribution is the target posterior. Metropolis-Hastings and Gibbs sampling are common variants.",
        "Bayesian model comparison uses the marginal likelihood (evidence) P(data|model) to select among competing models, automatically penalizing complexity without requiring separate regularization.",
    ],
    "Hypothesis Testing": [
        "A hypothesis test evaluates a null hypothesis H0 against an alternative H1 using sample data. The p-value is the probability of observing data as extreme as the sample under H0; small p-values provide evidence against H0.",
        "Type I error (false positive) occurs when H0 is true but rejected. Type II error (false negative) occurs when H0 is false but not rejected. The significance level alpha controls Type I error rate.",
        "The t-test compares means: one-sample tests whether a population mean equals a specified value, two-sample tests equality of two population means. It assumes approximately normal distributions or large samples.",
        "Multiple testing correction is necessary when performing many simultaneous tests. The Bonferroni correction divides alpha by the number of tests; the Benjamini-Hochberg procedure controls the false discovery rate.",
    ],
    "Confidence Intervals": [
        "A 95% confidence interval means that if we repeated the sampling procedure many times, approximately 95% of the constructed intervals would contain the true parameter value. It quantifies estimation uncertainty.",
        "For a normal population with known variance, the CI for the mean is x_bar +/- z_{alpha/2} * sigma/sqrt(n). The width decreases with sample size n, reflecting increased precision from more data.",
        "Bootstrap confidence intervals resample with replacement from the observed data to empirically approximate the sampling distribution, avoiding parametric assumptions about the underlying population.",
        "The margin of error is half the width of a confidence interval. For proportions, it is maximized at p = 0.5 and decreases as the sample proportion moves toward 0 or 1.",
    ],
    "Newton's Laws": [
        "Newton's first law (inertia): an object remains at rest or in uniform motion unless acted upon by a net external force. This defines inertial reference frames where the laws of mechanics hold without pseudo-forces.",
        "Newton's second law F = ma relates net force to mass and acceleration. For variable mass systems like rockets, the generalized form F = dp/dt (rate of change of momentum) is required.",
        "Newton's third law states that forces come in equal and opposite action-reaction pairs acting on different bodies. This is fundamental to deriving conservation of momentum in isolated systems.",
        "Free body diagrams isolate an object and show all forces acting on it: gravity, normal force, friction, tension, applied forces. Resolving into components along chosen axes converts to scalar equations for solution.",
    ],
    "Conservation of Energy": [
        "The work-energy theorem states that net work done on a particle equals its change in kinetic energy: W_net = Delta(KE) = (1/2)mv_f^2 - (1/2)mv_i^2. This connects force and displacement to motion.",
        "In conservative force fields (gravity, springs), a potential energy function U exists such that F = -dU/dx. Total mechanical energy E = KE + U is conserved when only conservative forces do work.",
        "Power is the rate of doing work: P = dW/dt = F dot v. In rotational systems, P = tau * omega where tau is torque and omega is angular velocity.",
        "Non-conservative forces like friction convert mechanical energy to thermal energy. The work done by friction equals the decrease in mechanical energy: W_friction = Delta(KE) + Delta(PE).",
    ],
    "Rotational Dynamics": [
        "The moment of inertia I = sum(m_i * r_i^2) measures resistance to angular acceleration, analogous to mass in linear dynamics. It depends on mass distribution relative to the rotation axis.",
        "Newton's second law for rotation: tau_net = I * alpha, where tau is torque, I is moment of inertia, and alpha is angular acceleration. This governs how angular velocity changes under applied torques.",
        "The parallel axis theorem states I = I_cm + M*d^2, where I_cm is the moment about the center of mass and d is the distance between the parallel axes. This simplifies calculation for off-center rotations.",
        "Angular momentum L = I*omega is conserved in the absence of external torque. This explains phenomena like a spinning ice skater accelerating when pulling in their arms (I decreases, omega increases).",
    ],
    "Maxwell's Equations": [
        "Gauss's law for electricity states that the electric flux through a closed surface equals the enclosed charge divided by epsilon_0: the divergence of E equals rho/epsilon_0.",
        "Faraday's law of induction states that a time-varying magnetic flux through a loop induces an electromotive force: curl(E) = -dB/dt. This is the operating principle of transformers and generators.",
        "Ampere's law with Maxwell's correction states that the curl of B equals mu_0*(J + epsilon_0 * dE/dt). The displacement current term dE/dt was Maxwell's key insight predicting electromagnetic waves.",
        "Together, Maxwell's equations predict electromagnetic waves propagating at speed c = 1/sqrt(mu_0 * epsilon_0) = 3 x 10^8 m/s, unifying electricity, magnetism, and optics into a single framework.",
    ],
    "Electromagnetic Waves": [
        "An electromagnetic wave consists of oscillating electric and magnetic fields perpendicular to each other and to the direction of propagation. The fields are in phase and satisfy E/B = c.",
        "The electromagnetic spectrum spans from radio waves (wavelength ~ km) through microwaves, infrared, visible light, ultraviolet, X-rays, to gamma rays (wavelength ~ pm). All travel at c in vacuum.",
        "The Poynting vector S = (1/mu_0) * E x B gives the power per unit area carried by an electromagnetic wave. Its time-average equals the intensity I = (1/2) * c * epsilon_0 * E_0^2.",
        "Polarization describes the orientation of the electric field oscillation. Linear polarization has E oscillating in a fixed plane; circular polarization has E rotating with constant magnitude.",
    ],
    "Gauss's Law": [
        "Gauss's law relates the net electric flux through a closed surface to the enclosed charge: Phi_E = Q_enc / epsilon_0. Its power lies in exploiting symmetry to compute E for symmetric charge distributions.",
        "For a uniformly charged sphere, Gauss's law with a spherical Gaussian surface gives E = kQ/r^2 outside (identical to a point charge) and E = kQr/R^3 inside (linearly increasing).",
        "For an infinite line charge with linear charge density lambda, a cylindrical Gaussian surface yields E = lambda / (2*pi*epsilon_0*r), directed radially outward from the line.",
        "Gauss's law for magnetism states that the net magnetic flux through any closed surface is zero: div(B) = 0. This reflects the fact that magnetic monopoles do not exist; field lines always form closed loops.",
    ],
}

# Question templates per topic
QUESTION_TEMPLATES = [
    "What is the time complexity of {topic}?",
    "Explain the key concepts of {topic}.",
    "How does {topic} work in practice?",
    "What are the advantages and disadvantages of {topic}?",
    "Compare and contrast different approaches to {topic}.",
    "Give an example that demonstrates {topic}.",
    "What is the mathematical foundation of {topic}?",
    "How is {topic} applied in real-world systems?",
    "What are common mistakes when implementing {topic}?",
    "Describe the relationship between {topic} and related concepts.",
]

DIFFICULTIES = ["foundational", "intermediate", "advanced"]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def sql_escape(text: str) -> str:
    """Escape single quotes for SQL string literals."""
    return text.replace("'", "''")


def sha256(text: str) -> str:
    """SHA-256 hash of normalized (lowercased, stripped) text."""
    return hashlib.sha256(text.strip().lower().encode()).hexdigest()


def format_vector(vec: np.ndarray) -> str:
    """Format numpy array as pgvector literal '[0.1,0.2,...]'."""
    return "[" + ",".join(f"{v:.6f}" for v in vec) + "]"


def random_timestamp(start: datetime, end: datetime) -> str:
    """Random timestamp between start and end as ISO string."""
    delta = end - start
    offset = random.random() * delta.total_seconds()
    ts = start + timedelta(seconds=offset)
    return ts.strftime("%Y-%m-%d %H:%M:%S+03")


# ─── Main generation ─────────────────────────────────────────────────────────

def main():
    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    # Time window for data
    start_date = datetime(2025, 9, 1, tzinfo=timezone.utc)
    end_date = datetime(2026, 4, 30, tzinfo=timezone.utc)

    sql_lines = []
    sql_lines.append("-- =====================================================")
    sql_lines.append("-- CiteBud Seed Data (auto-generated by seed_data.py)")
    sql_lines.append("-- =====================================================")
    sql_lines.append("")

    # ─── 1. Students ─────────────────────────────────────────────────────
    print(f"Generating {NUM_STUDENTS} students...")
    students = []
    for i in range(1, NUM_STUDENTS + 1):
        name = fake.name()
        email = f"{name.lower().replace(' ', '.').replace('-', '')}@university.edu"
        created = random_timestamp(start_date, start_date + timedelta(days=30))
        students.append((i, email, name, created))

    sql_lines.append("-- Students")
    for s in students:
        sql_lines.append(
            f"INSERT INTO students (student_id, email, full_name, created_at) "
            f"VALUES ({s[0]}, '{sql_escape(s[1])}', '{sql_escape(s[2])}', '{s[3]}');"
        )
    sql_lines.append(f"SELECT setval('students_student_id_seq', {NUM_STUDENTS});")
    sql_lines.append("")

    # ─── 2. Documents ────────────────────────────────────────────────────
    print(f"Generating {NUM_DOCUMENTS} documents...")
    documents = []
    doc_id = 0
    for i in range(NUM_DOCUMENTS):
        doc_id += 1
        student_id = random.randint(1, NUM_STUDENTS)
        course_code, course_name = random.choice(COURSES)
        week = random.randint(1, 14)
        title = f"{course_name} - Week {week} Notes"
        created = random_timestamp(start_date + timedelta(days=30), end_date - timedelta(days=60))
        documents.append((doc_id, student_id, title, course_code, created))

    sql_lines.append("-- Documents")
    for d in documents:
        sql_lines.append(
            f"INSERT INTO documents (document_id, student_id, title, course_code, created_at) "
            f"VALUES ({d[0]}, {d[1]}, '{sql_escape(d[2])}', '{d[3]}', '{d[4]}');"
        )
    sql_lines.append(f"SELECT setval('documents_document_id_seq', {doc_id});")
    sql_lines.append("")

    # ─── 3. Document Versions ────────────────────────────────────────────
    print("Generating document versions...")
    versions = []
    ver_id = 0
    for d in documents:
        num_versions = random.choices([1, 2], weights=[0.8, 0.2])[0]
        for v in range(1, num_versions + 1):
            ver_id += 1
            num_pages = random.randint(3, 25)
            file_path = f"/uploads/{d[1]}/{d[0]}/v{v}.pdf"
            uploaded = random_timestamp(
                datetime.fromisoformat(d[4].replace("+03", "+03:00")),
                end_date
            )
            versions.append((ver_id, d[0], v, file_path, num_pages, uploaded))

    sql_lines.append("-- Document Versions")
    for v in versions:
        sql_lines.append(
            f"INSERT INTO document_versions (version_id, document_id, version_no, file_path, num_pages, uploaded_at) "
            f"VALUES ({v[0]}, {v[1]}, {v[2]}, '{sql_escape(v[3])}', {v[4]}, '{v[5]}');"
        )
    sql_lines.append(f"SELECT setval('document_versions_version_id_seq', {ver_id});")
    sql_lines.append("")

    # ─── 4. Topics ───────────────────────────────────────────────────────
    print(f"Generating {NUM_TOPICS} topics...")
    sql_lines.append("-- Topics")
    for i, name in enumerate(TOPIC_NAMES[:NUM_TOPICS], 1):
        sql_lines.append(
            f"INSERT INTO topics (topic_id, name) VALUES ({i}, '{sql_escape(name)}');"
        )
    sql_lines.append(f"SELECT setval('topics_topic_id_seq', {NUM_TOPICS});")
    sql_lines.append("")

    # ─── 5. Chunks (with real embeddings) ────────────────────────────────
    print(f"Generating ~{TARGET_CHUNKS} chunks with embeddings (this may take a moment)...")
    chunks = []
    chunk_id = 0

    # Gather all chunk texts first for batch embedding
    chunk_texts = []
    chunk_metadata = []  # (version_id, chunk_index, page_number)

    for v in versions:
        version_id = v[0]
        num_pages = v[4]
        # Generate ~13 chunks per version on average to reach target
        num_chunks = random.randint(8, 18)
        # Pick topics for this document version
        doc_topics = random.sample(range(NUM_TOPICS), min(random.randint(2, 5), NUM_TOPICS))

        for ci in range(num_chunks):
            # Pick a topic and get a chunk text from that topic
            topic_idx = random.choice(doc_topics)
            topic_name = TOPIC_NAMES[topic_idx]
            templates = CHUNK_TEMPLATES.get(topic_name, CHUNK_TEMPLATES["Binary Search Trees"])
            text = random.choice(templates)
            # Add slight variation
            if random.random() < 0.3:
                text = text + f" This concept is fundamental to understanding {topic_name} in depth."

            page = random.randint(1, num_pages)
            chunk_texts.append(text)
            chunk_metadata.append((version_id, ci, page, text, topic_idx))

            if len(chunk_texts) >= TARGET_CHUNKS:
                break
        if len(chunk_texts) >= TARGET_CHUNKS:
            break

    # Batch encode all chunk texts
    print(f"  Encoding {len(chunk_texts)} chunks...")
    embeddings = model.encode(chunk_texts, show_progress_bar=True, batch_size=64)

    sql_lines.append("-- Chunks")
    chunk_topic_pairs = []  # for chunk_topics table
    for i, (meta, emb) in enumerate(zip(chunk_metadata, embeddings)):
        chunk_id = i + 1
        version_id, chunk_index, page, text, topic_idx = meta
        token_count = len(text.split())
        vec_str = format_vector(emb)

        sql_lines.append(
            f"INSERT INTO chunks (chunk_id, version_id, chunk_index, page_number, content, token_count, embedding) "
            f"VALUES ({chunk_id}, {version_id}, {chunk_index}, {page}, "
            f"'{sql_escape(text)}', {token_count}, '{vec_str}');"
        )

        # Track topic assignment for chunk_topics
        # Primary topic
        chunk_topic_pairs.append((chunk_id, topic_idx + 1, round(random.uniform(0.7, 1.0), 3)))
        # Sometimes add a secondary topic
        if random.random() < 0.5:
            secondary = random.randint(1, NUM_TOPICS)
            if secondary != topic_idx + 1:
                chunk_topic_pairs.append((chunk_id, secondary, round(random.uniform(0.3, 0.7), 3)))

    sql_lines.append(f"SELECT setval('chunks_chunk_id_seq', {chunk_id});")
    sql_lines.append("")

    # ─── 6. Chunk Topics ─────────────────────────────────────────────────
    print(f"Generating {len(chunk_topic_pairs)} chunk-topic pairs...")
    sql_lines.append("-- Chunk Topics")
    # Deduplicate
    seen_ct = set()
    for ct in chunk_topic_pairs:
        key = (ct[0], ct[1])
        if key not in seen_ct:
            seen_ct.add(key)
            sql_lines.append(
                f"INSERT INTO chunk_topics (chunk_id, topic_id, relevance) "
                f"VALUES ({ct[0]}, {ct[1]}, {ct[2]});"
            )
    sql_lines.append("")

    # ─── 7. Solutions ────────────────────────────────────────────────────
    print(f"Generating {NUM_SOLUTIONS} solutions...")
    solutions = []
    for i in range(1, NUM_SOLUTIONS + 1):
        topic_name = random.choice(TOPIC_NAMES[:NUM_TOPICS])
        question = random.choice(QUESTION_TEMPLATES).format(topic=topic_name)
        q_hash = sha256(question)
        difficulty = random.choice(DIFFICULTIES)
        answer = f"Based on the retrieved source materials, here is a {difficulty}-level explanation of {topic_name}: {random.choice(CHUNK_TEMPLATES.get(topic_name, CHUNK_TEMPLATES['Binary Search Trees']))}"
        model_name = random.choice(["gpt-4o-mini", "gpt-4o", "claude-3-haiku"])
        generated = random_timestamp(start_date + timedelta(days=60), end_date)
        solutions.append((i, q_hash, difficulty, answer, model_name, generated, question))

    sql_lines.append("-- Solutions")
    for s in solutions:
        sql_lines.append(
            f"INSERT INTO solutions (solution_id, question_hash, difficulty, answer_text, model_name, generated_at) "
            f"VALUES ({s[0]}, '{s[1]}', '{s[2]}', '{sql_escape(s[3])}', '{s[4]}', '{s[5]}');"
        )
    sql_lines.append(f"SELECT setval('solutions_solution_id_seq', {NUM_SOLUTIONS});")
    sql_lines.append("")

    # ─── 8. Queries ──────────────────────────────────────────────────────
    print(f"Generating {NUM_QUERIES} queries...")
    queries = []
    for i in range(1, NUM_QUERIES + 1):
        student_id = random.randint(1, NUM_STUDENTS)
        # Some queries hit cache (reuse an existing solution)
        sol = random.choice(solutions)
        question = sol[6]  # same question as the solution
        q_hash = sol[1]
        difficulty = sol[2]
        solution_id = sol[0]
        was_cache_hit = random.random() < 0.35
        asked = random_timestamp(
            datetime.fromisoformat(sol[5].replace("+03", "+03:00")),
            end_date
        )
        queries.append((i, student_id, question, q_hash, difficulty, solution_id, was_cache_hit, asked))

    sql_lines.append("-- Queries")
    for q in queries:
        cache_str = "TRUE" if q[6] else "FALSE"
        sql_lines.append(
            f"INSERT INTO queries (query_id, student_id, question_text, question_hash, difficulty, solution_id, was_cache_hit, asked_at) "
            f"VALUES ({q[0]}, {q[1]}, '{sql_escape(q[2])}', '{q[3]}', '{q[4]}', {q[5]}, {cache_str}, '{q[7]}');"
        )
    sql_lines.append(f"SELECT setval('queries_query_id_seq', {NUM_QUERIES});")
    sql_lines.append("")

    # ─── 9. Solution Citations ───────────────────────────────────────────
    print("Generating solution citations...")
    sql_lines.append("-- Solution Citations")
    citation_count = 0
    for sol in solutions:
        sol_id = sol[0]
        num_citations = random.randint(2, 5)
        cited_chunks = random.sample(range(1, chunk_id + 1), min(num_citations, chunk_id))
        for rank, cid in enumerate(cited_chunks, 1):
            sim_score = round(random.uniform(0.55, 0.98), 4)
            sql_lines.append(
                f"INSERT INTO solution_citations (solution_id, chunk_id, rank, similarity_score) "
                f"VALUES ({sol_id}, {cid}, {rank}, {sim_score});"
            )
            citation_count += 1
    sql_lines.append("")

    # ─── 10. Feedback ────────────────────────────────────────────────────
    print("Generating feedback...")
    sql_lines.append("-- Feedback")
    feedback_queries = random.sample(range(1, NUM_QUERIES + 1), min(80, NUM_QUERIES))
    for fb_id, qid in enumerate(sorted(feedback_queries), 1):
        rating = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 20, 35, 30])[0]
        comment = ""
        if random.random() < 0.4:
            comments = [
                "Very helpful explanation!", "Could use more detail.",
                "The citations were spot on.", "Too basic for my level.",
                "Great breakdown of the concept.", "Needs more examples.",
                "Perfect difficulty level.", "Answer was too long.",
                "Exactly what I needed for revision.", "Some parts were unclear.",
            ]
            comment = random.choice(comments)
        q = queries[qid - 1]
        created = random_timestamp(
            datetime.fromisoformat(q[7].replace("+03", "+03:00")),
            end_date
        )
        comment_sql = f", '{sql_escape(comment)}'" if comment else ", NULL"
        sql_lines.append(
            f"INSERT INTO feedback (feedback_id, query_id, rating, comment, created_at) "
            f"VALUES ({fb_id}, {qid}, {rating}{comment_sql}, '{created}');"
        )
    sql_lines.append(f"SELECT setval('feedback_feedback_id_seq', {len(feedback_queries)});")
    sql_lines.append("")

    # ─── 11. User Topic Profile ──────────────────────────────────────────
    print("Generating user topic profiles...")
    sql_lines.append("-- User Topic Profiles")
    profile_pairs = set()
    while len(profile_pairs) < 100:
        sid = random.randint(1, NUM_STUDENTS)
        tid = random.randint(1, NUM_TOPICS)
        profile_pairs.add((sid, tid))

    for sid, tid in sorted(profile_pairs):
        confidence = round(random.uniform(0.1, 0.95), 3)
        interactions = random.randint(1, 50)
        updated = random_timestamp(end_date - timedelta(days=30), end_date)
        sql_lines.append(
            f"INSERT INTO user_topic_profile (student_id, topic_id, confidence_score, interactions_count, updated_at) "
            f"VALUES ({sid}, {tid}, {confidence}, {interactions}, '{updated}');"
        )
    sql_lines.append("")

    # ─── Write output ────────────────────────────────────────────────────
    sql_lines.append("-- =====================================================")
    sql_lines.append("-- Seed complete.")
    sql_lines.append(f"-- Total chunks: {chunk_id}")
    sql_lines.append(f"-- Total chunk_topics: {len(seen_ct)}")
    sql_lines.append(f"-- Total citations: {citation_count}")
    sql_lines.append("-- =====================================================")

    output = "\n".join(sql_lines)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"\nDone! Wrote {OUTPUT_PATH} ({len(sql_lines)} lines)")
    print(f"  Students:        {NUM_STUDENTS}")
    print(f"  Documents:       {NUM_DOCUMENTS}")
    print(f"  Versions:        {len(versions)}")
    print(f"  Chunks:          {chunk_id}")
    print(f"  Topics:          {NUM_TOPICS}")
    print(f"  Chunk-Topics:    {len(seen_ct)}")
    print(f"  Solutions:       {NUM_SOLUTIONS}")
    print(f"  Queries:         {NUM_QUERIES}")
    print(f"  Citations:       {citation_count}")
    print(f"  Feedback:        {len(feedback_queries)}")
    print(f"  Topic Profiles:  {len(profile_pairs)}")
    total = NUM_STUDENTS + NUM_DOCUMENTS + len(versions) + chunk_id + NUM_TOPICS + len(seen_ct) + NUM_SOLUTIONS + NUM_QUERIES + citation_count + len(feedback_queries) + len(profile_pairs)
    print(f"  TOTAL ROWS:      {total}")


if __name__ == "__main__":
    main()
