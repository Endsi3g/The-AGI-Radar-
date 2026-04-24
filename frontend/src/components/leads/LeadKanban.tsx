"use client";

import { useState } from "react";
import { DragDropContext, Droppable, Draggable, DropResult } from "@hello-pangea/dnd";
import Link from "next/link";
import { MapPin, Star, MoreVertical } from "lucide-react";
import type { Lead, LeadStatus } from "@/types/lead";
import { PIPELINE_COLUMNS, STATUS_LABELS, STATUS_DOT, SOURCE_ICONS } from "@/types/lead";
import { LeadScoreBadge } from "./LeadScoreBadge";
import { useUpdateLead } from "@/hooks/useLeads";

interface Props {
  leads: Lead[];
}

function groupByStatus(leads: Lead[]): Record<LeadStatus, Lead[]> {
  const groups = Object.fromEntries(
    PIPELINE_COLUMNS.map((s) => [s, [] as Lead[]])
  ) as Record<LeadStatus, Lead[]>;
  for (const lead of leads) {
    if (groups[lead.status]) {
      groups[lead.status].push(lead);
    }
  }
  return groups;
}

export function LeadKanban({ leads }: Props) {
  const updateLead = useUpdateLead();
  const [columns, setColumns] = useState<Record<LeadStatus, Lead[]>>(groupByStatus(leads));

  // Sync when leads prop changes (e.g., after refetch)
  if (leads.length !== Object.values(columns).flat().length) {
    const fresh = groupByStatus(leads);
    // Only update if actually different
    if (JSON.stringify(fresh) !== JSON.stringify(columns)) {
      setColumns(fresh);
    }
  }

  const onDragEnd = (result: DropResult) => {
    const { source, destination, draggableId } = result;
    if (!destination) return;
    if (source.droppableId === destination.droppableId && source.index === destination.index) return;

    const srcStatus = source.droppableId as LeadStatus;
    const dstStatus = destination.droppableId as LeadStatus;

    // Optimistic update
    const newCols = { ...columns };
    const [moved] = newCols[srcStatus].splice(source.index, 1);
    newCols[dstStatus] = [...newCols[dstStatus]];
    newCols[dstStatus].splice(destination.index, 0, { ...moved, status: dstStatus });
    setColumns(newCols);

    // Persist to API
    updateLead.mutate({ id: draggableId, data: { status: dstStatus } });
  };

  return (
    <DragDropContext onDragEnd={onDragEnd}>
      <div className="flex gap-4 overflow-x-auto pb-4">
        {PIPELINE_COLUMNS.map((status) => {
          const col = columns[status] || [];
          return (
            <div key={status} className="flex-none w-72">
              {/* Column header */}
              <div className="flex items-center gap-2 mb-3 px-1">
                <span className={`w-2.5 h-2.5 rounded-full ${STATUS_DOT[status]}`} />
                <span className="font-semibold text-gray-700 text-sm">{STATUS_LABELS[status]}</span>
                <span className="ml-auto text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium">
                  {col.length}
                </span>
              </div>

              <Droppable droppableId={status}>
                {(provided, snapshot) => (
                  <div
                    ref={provided.innerRef}
                    {...provided.droppableProps}
                    className={`min-h-24 rounded-xl p-2 space-y-2 transition-colors ${
                      snapshot.isDraggingOver ? "bg-blue-50 border-2 border-blue-200 border-dashed" : "bg-gray-50"
                    }`}
                  >
                    {col.map((lead, index) => (
                      <Draggable key={lead.id} draggableId={lead.id} index={index}>
                        {(drag, dragSnapshot) => (
                          <div
                            ref={drag.innerRef}
                            {...drag.draggableProps}
                            {...drag.dragHandleProps}
                            className={`bg-white rounded-lg border p-3 cursor-grab active:cursor-grabbing transition-shadow ${
                              dragSnapshot.isDragging ? "shadow-lg border-blue-300 rotate-1" : "border-gray-200 hover:border-gray-300 hover:shadow-sm"
                            }`}
                          >
                            {/* Card top */}
                            <div className="flex items-start justify-between gap-1 mb-2">
                              <Link
                                href={`/leads/${lead.id}`}
                                onClick={(e) => e.stopPropagation()}
                                className="font-medium text-sm text-gray-900 hover:text-blue-600 line-clamp-2 leading-snug"
                              >
                                {lead.business_name}
                              </Link>
                              <LeadScoreBadge score={lead.ai_score} size="sm" />
                            </div>

                            {/* Industry */}
                            {lead.industry && (
                              <p className="text-xs text-gray-400 capitalize mb-2">{lead.industry}</p>
                            )}

                            {/* City */}
                            {lead.city && (
                              <div className="flex items-center gap-1 text-xs text-gray-500 mb-2">
                                <MapPin size={11} />
                                {lead.city}
                              </div>
                            )}

                            {/* Google rating */}
                            {lead.google_rating && (
                              <div className="flex items-center gap-1 text-xs text-amber-500 mb-2">
                                <Star size={11} fill="currentColor" />
                                {lead.google_rating}
                                {lead.google_reviews && (
                                  <span className="text-gray-400">({lead.google_reviews})</span>
                                )}
                              </div>
                            )}

                            {/* Sources */}
                            {lead.source_flags.length > 0 && (
                              <div className="flex gap-1 mt-2 pt-2 border-t border-gray-50">
                                {lead.source_flags.map((src) => (
                                  <span key={src} title={src} className="text-sm">
                                    {SOURCE_ICONS[src] || "🔗"}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </Draggable>
                    ))}
                    {provided.placeholder}

                    {col.length === 0 && !snapshot.isDraggingOver && (
                      <p className="text-xs text-gray-400 text-center py-4">
                        Glisser un lead ici
                      </p>
                    )}
                  </div>
                )}
              </Droppable>
            </div>
          );
        })}
      </div>
    </DragDropContext>
  );
}
