"""Region settings: which Z-Anatomy objects belong to this model.
Change ACTIVE (or edit a dict) to build another region. Z-Anatomy world, metres;
right side is x < 0, +z is up, +y is posterior.
SHOULDER selects everything in a box (right side only); LUMBAR (whitelist=True) selects
named structures on BOTH sides."""
import re

SHOULDER = dict(
    name='shoulder',
    # neck root (top of C4 = 1.506) down to the proximal third of the forearm
    # (radius 0.856-1.093 -> 1.093 - 0.237/3 = 1.014)
    z_lo=1.014, z_hi=1.51,
    x_max=-0.03,              # centre must be right of this (midline is 0)
    bones=r'^(Clavicle|Scapula|Humerus|Radius|Ulna)$',
    context_bones=r'^(Manubrium of sternum|Body of sternum|Xiphoid process|'
                  r'Vertebra (C[4-7]|T[1-8])|(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth) rib|'
                  r'Costal cartilage of (first|second|third|fourth|fifth|sixth|seventh|eighth) rib)$',
    # whole muscles that move the shoulder girdle, kept even outside the box
    whole_muscles=r'trapezius|latissimus|serratus anterior|pectoralis (major|minor)|'
                  r'levator scapulae|rhomboid|scalen|omohyoid|subclavius',
    # lymph node groups wanted from system 6
    nodes=r'axillary|infraclavicular|interpectoral|brachial|cubital|deltopectoral',
    # trunk, neck and visceral structures that fall inside the box but are not wanted
    exclude=r'intercostal|costal|sternocleid|platysma|thyro|laryn|pharyn|trache|oesoph|'
            r'thoracic duct|vertebral|carotid|jugular|vag|phrenic|sympath|cardiac|pulmon|'
            r'aort|abdomin|oblique|rectus|spinal (cord|nerve)|spinalis|spinous|erector|longissimus|iliocostal|'
            r'semispinal|multifid|rotatores|splenius|serratus posterior|levatores|transversus|'
            r'subcostal|diaphragm|mamm|breast|thyroid|cervical plexus|ansa|hypoglos|'
            r'internal thoracic|pericardiacophrenic|brachiocephalic|azygos|intervertebral|'
            r'longus|rib|sternum|sternal|interspinal|intertransvers|nuchal|supraspinous lig|'
            r'cervical (vein|artery|nerve)|occipital|auricular|facial|lingual|lumbar|iliac|'
            r'scalene tubercle|hand|digit|finger|thumb|palm|carp|metacarp|wrist|renal|iliohypogas|'
            r'quadratus lumborum|epigastric|hypochondri|umbilical|of abdomen|submandibular|'
            r'costocervical|investing cervical|femoral|gluteal|inguinal',
    exclude_keep=r'transverse humeral|transverse scapular|serratus anterior|'
                 r'superficial cervical artery|transverse cervical|dorsal scapular|'
                 r'suprascapular|subclavian|(?<!femoral )cutaneous|thyrocervical',   # not the lateral femoral cutaneous n. (thigh)
    # always kept (right SC joint sits near the midline; subclavian vessels are named 'Right ...')
    always=r'^(Right subclavian (artery|vein)|.*sternoclavicular.*\.r|Interclavicular ligament\.r)$',
    # nerves/vessels with these names are kept whole if they reach into the box
    limb_names=r'antebrachial|cutaneous|radial|ulnar|median|interosseous|cephalic|basilic|cubital|recurrent',
    # forearm muscles arising at the elbow (top above elbow_top, centre lateral to limb_x) kept whole
    limb_x=-0.17, elbow_top=1.05,
    sides=r'\.[a-z0-9]*r$',   # right-side suffixes: .r .or .er .e2r
    systems=(1, 2, 3, 4, 5, 6, 7, 9),
    budget=600000,
    # only the ghosted context bones may be decimated to meet the budget
    reduce_dev=0.0003,
    # coarse in the source: one Loop subdivision level, shape change <= 0.3 mm
    smooth=r'^(Supraspinatus muscle|Infraspinatus muscle|Subscapularis muscle|Teres minor muscle|'
           r'Articular capsule of glenohumeral joint|(Superior|Middle|Inferior) glenohumeral ligament|'
           r'Glenoid labrum|Coracohumeral ligament|Coraco-acromial ligament|Long head of biceps brachii)$',
    centre='glenohumeral',    # viewer recentres here (Phase B)
)

LUMBAR = dict(
    name='lumbar', glb='lumbar.glb', whitelist=True, both_sides=True, split=True,
    # top of L1 (1.134) to the coccyx (0.830); measured on Z-Anatomy Vertebra L1 / Coccyx bounding boxes
    z_lo=0.830, z_hi=1.134,
    bones=r'^(Vertebra L[345]|Sacrum)$',
    context_bones=r'^(Vertebra L[12]|Hip bone|Coccyx|Intervertebral disc (L1-L2|L2-L3)|Nucleus pulposus (L1-L2|L2-L3))$',
    discs=r'^(Intervertebral disc|Nucleus pulposus) (L3-L4|L4-L5|L5-S1)$',
    ligaments=r'^(Anterior longitudinal ligament|Posterior longitudinal ligament|Ligamenta flava|Interspinous ligaments|'
              r'Supraspinous ligament|Intertransverse ligaments|Iliolumbar ligament|(Anterior|Interosseous|Posterior) sacro-iliac ligament|'
              r'Sacrococcygeal symphysis|Intercornual ligament)$',
    muscles=r'^(Multifidus lumborum muscle|Iliocostalis lumborum muscle|Longissimus thoracis muscle|Spinalis thoracis muscle|'
            r'Rotatores|Interspinales lumborum muscles|(Dorsal|Ventral) parts of lateral intertransversarii lumborum muscles|'
            r'Quadratus lumborum muscle|Psoas major|(Anterior|Middle|Posterior) layer of thoracolumbar fascia)$',
    # origin/insertion footprints of the muscles above (system 2), kept when their centre is inside z_lo..z_hi
    attachments=r'^(Multifidus lumborum muscle|Erector spinae|Iliocostalis lumborum muscle|Longissimus thoracis muscle|'
                r'Interspinales lumborum muscles|Quadratus lumborum muscle|Psoas major)$',
    vessels=r'^(Abdominal aorta|Inferior vena cava \(abdominal part\)|Common iliac (artery|vein)|Median sacral artery|'
            r'Lumbar (arteries|veins)|Iliolumbar (artery|vein)|(Iliacus|Lumbar|Spinal) branch of iliolumbar artery|'
            r'(Left|Right) ascending lumbar vein|Lateral sacral veins)$',
    neural=r'^(Spinal dura|Cauda equina|Anterior root of spinal nerve|Posterior root of spinal nerve|Spinal ganglion|'
           r'White matter of spinal cord)$',
    nerves=r'^(Iliohypogastric nerve|Ilio-inguinal nerve|Genitofemoral nerve|(Femoral|Genital) branch of genitofemoral nerve|'
           r'Obturator nerve|Femoral nerve|Lateral femoral cutaneous nerve|Superior gluteal nerve|Nerve to piriformis muscle|'
           r'Nerve to quadratus femoris muscle|(Anterior|Posterior) root of posterior femoral cutaneous nerve|'
           r'Posterior femoral cutaneous nerve|Sciatic nerve|Pudendal nerve)$',
    skin=r'^(Lumbar region|Sacral region|Vertebral region)$',
    # objects that run up the whole spine: cut at z_hi (top of L1)
    crop_top=r'^(Anterior longitudinal ligament|Posterior longitudinal ligament|Ligamenta flava|Interspinous ligaments|'
             r'Supraspinous ligament|Intertransverse ligaments|Rotatores|Spinal dura|Anterior root of spinal nerve|'
             r'Posterior root of spinal nerve|Spinal ganglion|White matter of spinal cord|Vertebral region)$',
    # nerves leaving the pelvis: cut at nerve_exit_z. Femoral n. passes under the inguinal ligament at z 0.870,
    # sciatic n. leaves under piriformis at 0.872 (nearest points, both sides)
    crop_nerves=r'^(Femoral nerve|Lateral femoral cutaneous nerve|Obturator nerve|(Femoral|Genital) branch of genitofemoral nerve|'
                r'Ilio-inguinal nerve|Sciatic nerve|Posterior femoral cutaneous nerve|Nerve to quadratus femoris muscle|Pudendal nerve|'
                r'Superior gluteal nerve)$',
    nerve_exit_z=0.870,
    sides=r'\.[a-z0-9]*[rl]$',   # .r .l and footprint suffixes .or .el .e2r ...
    systems=(1, 2, 3, 4, 5, 7, 9),
    budget=600000,
    reduce_dev=0.0003,
    # only these may be decimated to meet the budget (context bones, then muscles far from L3-S1)
    reducible=r'^(Vertebra L[12]|Hip bone|Coccyx|Longissimus thoracis muscle|Iliocostalis lumborum muscle|Spinalis thoracis muscle|'
              r'Rotatores|Psoas major|Quadratus lumborum muscle)( \((left|right)\))?$',
    # coarse in the source: one Loop subdivision level, shape change <= 0.3 mm (SPEC step 5b)
    smooth=r'^(Ligamenta flava|Posterior longitudinal ligament|Anterior longitudinal ligament|Interspinous ligaments|'
           r'Supraspinous ligament|(Anterior|Posterior) root of spinal nerve|Cauda equina|Spinal ganglion|Spinal dura|'
           r'Intervertebral disc|Nucleus pulposus)( (L3-L4|L4-L5|L5-S1))?( \((left|right)\))?$',
    centre='L4-L5 disc',      # viewer recentres here (Phase B)
)

ACTIVE = LUMBAR
R = {k: re.compile(v, re.I) for k, v in ACTIVE.items() if isinstance(v, str) and k not in ('name', 'centre', 'glb')}
